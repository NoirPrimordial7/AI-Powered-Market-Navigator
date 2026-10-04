"""Release boundaries: exclude runtime state, reject secrets, preserve bytes."""
from pathlib import Path
import tempfile
import unittest
import zipfile
from scripts.build_release import ROOT,build,release_paths,validate_files

class ReleaseTests(unittest.TestCase):
    def test_runtime_and_secret_files_are_excluded(self):
        names={p.relative_to(ROOT).as_posix() for p in release_paths(ROOT)}
        self.assertIn('model3.h5',names)
        self.assertIn('scripts/build_release.py',names)
        self.assertTrue(all(not p.startswith(('.cache/','.tmp/','.venv/','__pycache__/','training-runs/','dist/')) for p in names))
        self.assertNotIn('.streamlit/secrets.toml',names)

    def test_secret_detection_stops_release_without_printing_value(self):
        scratch=ROOT/'.tmp';scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            path=Path(directory)/'unsafe.py'
            fake='sk-'+'or-v1-'+'a'*64
            path.write_text(fake,encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'Potential credential in unsafe.py') as context:validate_files([path])
            self.assertNotIn(fake,str(context.exception))

    def test_archive_is_deterministic_and_preserves_model(self):
        scratch=ROOT/'.tmp';scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            version='v'+(ROOT/'VERSION').read_text().strip()
            a=build(version,Path(directory)/'one')
            b=build(version,Path(directory)/'two')
            self.assertEqual(a['archive_sha256'],b['archive_sha256'])
            with zipfile.ZipFile(Path(directory)/'one'/a['archive']) as archive:
                self.assertEqual(archive.read(f'northstar-{version}/model3.h5'),(ROOT/'model3.h5').read_bytes())

    def test_wrong_version_cannot_be_released(self):
        with self.assertRaisesRegex(ValueError,'does not match VERSION'):build('v999.0.0',ROOT/'dist')
