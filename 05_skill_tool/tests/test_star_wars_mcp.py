"""Configuration tests for the Part 5 Star Wars MCP toolset."""

import unittest
from unittest.mock import patch

import agent


class StarWarsMcpTests(unittest.TestCase):
    @patch("agent.open_collection", return_value=object())
    def test_agent_registers_the_star_wars_and_course_note_toolsets(self, _open_collection):
        assistant = agent.CourseAssistant("test")

        self.assertEqual(agent.STAR_WARS_MCP_URL, "https://gateway.pipeworx.io/swapi/mcp")
        self.assertIn("search_course_notes", assistant.course_note_toolset.tools)
        self.assertIn("load_executive_brief_skill", assistant.skill_toolset.tools)
        self.assertEqual(assistant.star_wars_mcp.client.transport.url, agent.STAR_WARS_MCP_URL)
        self.assertIs(assistant.star_wars_toolset.wrapped, assistant.star_wars_mcp)


if __name__ == "__main__":
    unittest.main()
