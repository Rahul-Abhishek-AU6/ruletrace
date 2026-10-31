import json
import subprocess
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
TOOL = PROJECT / "ruletrace.py"

class RuleTraceTests(unittest.TestCase):
    def repo(self):
        directory = tempfile.TemporaryDirectory()
        root = Path(directory.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        return directory, root

    def run_scan(self, root, *extra):
        output = root / "receipt.json"
        proc = subprocess.run(["python3", str(TOOL), "scan", str(root), "--json", str(output), *extra], text=True, capture_output=True)
        return proc, json.loads(output.read_text())

    def test_recognizes_files_and_git_state(self):
        holder, root = self.repo()
        self.addCleanup(holder.cleanup)
        (root / "AGENTS.md").write_text("Use python3.\n")
        (root / "CLAUDE.md").write_text("Local notes.\n")
        (root / ".github").mkdir(); (root / ".github/copilot-instructions.md").write_text("Review.\n")
        (root / ".cursor/rules").mkdir(parents=True); (root / ".cursor/rules/style.md").write_text("Style.\n")
        subprocess.run(["git", "add", "."], cwd=root, check=True); subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
        (root / "CLAUDE.md").write_text("Changed.\n")
        proc, receipt = self.run_scan(root)
        self.assertEqual(proc.returncode, 0)
        states = {f["path"]: f["git_state"] for f in receipt["files"]}
        self.assertEqual(len(states), 4); self.assertEqual(states["AGENTS.md"], "tracked-clean")
        self.assertEqual(states["CLAUDE.md"], "tracked-modified")

    def test_imports_missing_escape_and_cycle_are_reported(self):
        holder, root = self.repo(); self.addCleanup(holder.cleanup)
        (root / "AGENTS.md").write_text("Read @CLAUDE.md\nRead @missing.md\nRead @../outside.md\n")
        (root / "CLAUDE.md").write_text("Read @AGENTS.md\n")
        proc, receipt = self.run_scan(root)
        self.assertEqual(proc.returncode, 0)
        kinds = {flag["category"] for flag in receipt["flags"]}
        self.assertTrue({"import-missing", "import-escapes-root", "import-cycle"}.issubset(kinds))

    def test_strict_fails_on_destructive_command_without_executing_it(self):
        holder, root = self.repo(); self.addCleanup(holder.cleanup)
        marker = root / "marker"
        (root / "AGENTS.md").write_text(f"Never run: rm -rf {marker}\n")
        proc, receipt = self.run_scan(root, "--strict")
        self.assertEqual(proc.returncode, 2); self.assertFalse(marker.exists())
        self.assertEqual(receipt["summary"]["high"], 1)

if __name__ == "__main__":
    unittest.main()
