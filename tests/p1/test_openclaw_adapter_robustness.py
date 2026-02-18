import unittest

from python.helpers.openclaw_adapter import (
    classify_model_output_shape,
    extract_tool_request,
    normalize_model_output,
    should_fallback_plain_response,
)


class OpenClawAdapterRobustnessTests(unittest.TestCase):
    def test_normalize_strips_fenced_json(self):
        raw = "```json\n{\"tool_name\":\"response\",\"tool_args\":{\"text\":\"ok\"}}\n```"
        normalized = normalize_model_output(raw)
        self.assertTrue(normalized.startswith('{"tool_name"'))
        self.assertFalse(normalized.startswith("```"))

    def test_classify_plain_response(self):
        msg = "Hello Steve, I can do that for you."
        self.assertEqual(classify_model_output_shape(msg), "plain_response")
        self.assertTrue(should_fallback_plain_response(msg))

    def test_classify_json_like_and_extract(self):
        msg = '{"tool_name":"response","tool_args":{"text":"done"}}'
        self.assertEqual(classify_model_output_shape(msg), "json_like")
        req = extract_tool_request(msg)
        self.assertIsInstance(req, dict)
        self.assertEqual(req.get("tool_name"), "response")
        self.assertFalse(should_fallback_plain_response(msg))

    def test_classify_malformed_json_like(self):
        msg = '{"tool_name":"response","tool_args":{"text":"broken"}'
        self.assertEqual(classify_model_output_shape(msg), "malformed_json_like")
        self.assertFalse(should_fallback_plain_response(msg))

    def test_classify_empty(self):
        self.assertEqual(classify_model_output_shape(" \n"), "empty")
        self.assertFalse(should_fallback_plain_response(" \n"))


if __name__ == "__main__":
    unittest.main()
