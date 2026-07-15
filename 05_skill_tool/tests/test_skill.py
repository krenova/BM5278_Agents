import unittest
from pathlib import Path
from skill_loader import load_skill
class SkillTests(unittest.TestCase):
 def test_load_skill(self):
  skill=load_skill(Path(__file__).parents[1]/'SKILL.md');self.assertIn('## Key points',skill);self.assertIn('## Risks',skill)
if __name__=='__main__':unittest.main()
