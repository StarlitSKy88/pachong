import unittest
from unittest.mock import patch, MagicMock, mock_open
from tools.llm_api import query_llm, load_environment
import os
import google.generativeai as genai
import io
import sys
import pytest
from unittest.mock import Mock

def is_llm_configured():
    """Check if LLM is configured by trying to connect to the server"""
    try:
        response = query_llm("test")
        return response is not None
    except:
        return False

# Skip all LLM tests if LLM is not configured
skip_llm_tests = not is_llm_configured()
skip_message = "Skipping LLM tests as LLM is not configured. This is normal if you haven't set up a local LLM server."

class TestEnvironmentLoading(unittest.TestCase):
    def setUp(self):
        # Save original environment
        self.original_env = dict(os.environ)
        # Clear environment variables we're testing
        for key in ['TEST_VAR']:
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch('pathlib.Path.exists')
    @patch('tools.llm_api.load_dotenv')
    @patch('builtins.open')
    def test_environment_loading_precedence(self, mock_open, mock_load_dotenv, mock_exists):
        # Mock all env files exist
        mock_exists.return_value = True
        
        # Mock file contents
        mock_file = MagicMock()
        mock_file.__enter__.return_value = io.StringIO('TEST_VAR=value\n')
        mock_open.return_value = mock_file
        
        # Mock different values for TEST_VAR in different files
        def load_dotenv_side_effect(dotenv_path, **kwargs):
            if '.env.local' in str(dotenv_path):
                os.environ['TEST_VAR'] = 'local'
            elif '.env' in str(dotenv_path):
                if 'TEST_VAR' not in os.environ:  # Only set if not already set
                    os.environ['TEST_VAR'] = 'default'
            elif '.env.example' in str(dotenv_path):
                if 'TEST_VAR' not in os.environ:  # Only set if not already set
                    os.environ['TEST_VAR'] = 'example'
        mock_load_dotenv.side_effect = load_dotenv_side_effect
        
        # Load environment
        load_environment()
        
        # Verify precedence (.env.local should win)
        self.assertEqual(os.environ.get('TEST_VAR'), 'local')
        
        # Verify order of loading
        calls = mock_load_dotenv.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertTrue(str(calls[0][1]['dotenv_path']).endswith('.env.local'))
        self.assertTrue(str(calls[1][1]['dotenv_path']).endswith('.env'))
        self.assertTrue(str(calls[2][1]['dotenv_path']).endswith('.env.example'))

    @patch('pathlib.Path.exists')
    @patch('tools.llm_api.load_dotenv')
    def test_environment_loading_no_files(self, mock_load_dotenv, mock_exists):
        # Mock no env files exist
        mock_exists.return_value = False
        
        # Load environment
        load_environment()
        
        # Verify load_dotenv was not called
        mock_load_dotenv.assert_not_called()

class TestLLMAPI(unittest.TestCase):
    def setUp(self):
        # Create mock clients for different providers
        self.mock_openai_client = MagicMock()
        self.mock_anthropic_client = MagicMock()
        
        # Set up OpenAI-style response
        self.mock_openai_response = MagicMock()
        self.mock_openai_choice = MagicMock()
        self.mock_openai_message = MagicMock()
        self.mock_openai_message.content = "Test OpenAI response"
        self.mock_openai_choice.message = self.mock_openai_message
        self.mock_openai_response.choices = [self.mock_openai_choice]
        self.mock_openai_client.chat.completions.create.return_value = self.mock_openai_response
        
        # Set up Anthropic-style response
        self.mock_anthropic_response = MagicMock()
        self.mock_anthropic_content = MagicMock()
        self.mock_anthropic_content.text = "Test Anthropic response"
        self.mock_anthropic_response.content = [self.mock_anthropic_content]
        self.mock_anthropic_client.messages.create.return_value = self.mock_anthropic_response
        
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key'
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch('tools.llm_api.OpenAI')
    def test_query_openai(self, mock_openai):
        mock_openai.return_value = self.mock_openai_client
        response = query_llm("Test prompt", provider="openai")
        self.assertEqual(response, "Test OpenAI response")
        self.mock_openai_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test prompt"}],
            max_tokens=1000
        )

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch('tools.llm_api.Anthropic')
    def test_query_anthropic(self, mock_anthropic):
        mock_anthropic.return_value = self.mock_anthropic_client
        response = query_llm("Test prompt", provider="anthropic")
        self.assertEqual(response, "Test Anthropic response")
        self.mock_anthropic_client.messages.create.assert_called_once_with(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": "Test prompt"}]
        )

    @unittest.skipIf(skip_llm_tests, skip_message)
    @patch('tools.llm_api.OpenAI')
    def test_query_llm_with_image(self, mock_openai):
        # 创建测试图片
        image_path = "test.jpg"
        with patch('builtins.open', mock_open(read_data=b"test image data")):
            mock_openai.return_value = self.mock_openai_client
            response = query_llm("Test prompt", provider="openai", image_path=image_path)
            self.assertEqual(response, "Test OpenAI response")
            self.mock_openai_client.chat.completions.create.assert_called_once()
            call_args = self.mock_openai_client.chat.completions.create.call_args[1]
            self.assertEqual(call_args["model"], "gpt-4-vision-preview")
            self.assertEqual(len(call_args["messages"][0]["content"]), 2)
            self.assertEqual(call_args["messages"][0]["content"][0]["text"], "Test prompt")
            self.assertIn("image_url", call_args["messages"][0]["content"][1])

    def test_query_llm_invalid_provider(self):
        with self.assertRaises(ValueError) as exc_info:
            query_llm("Test prompt", provider="invalid")
        self.assertIn("不支持的LLM提供商", str(exc_info.exception))

def test_load_environment(tmp_path):
    # 创建测试环境文件
    env_file = tmp_path / '.env'
    env_file.write_text('TEST_KEY=test_value\n')
    
    # 保存当前工作目录
    old_cwd = os.getcwd()
    try:
        # 切换到临时目录
        os.chdir(tmp_path)
        # 加载环境变量
        load_environment()
        # 验证环境变量是否被正确加载
        assert os.getenv('TEST_KEY') == 'test_value'
    finally:
        # 恢复工作目录
        os.chdir(old_cwd)

@patch('tools.llm_api.OpenAI')
def test_query_llm_openai(mock_openai):
    # 设置模拟响应
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="测试响应"))]
    mock_client.chat.completions.create.return_value = mock_response
    
    # 调用函数
    response = query_llm("测试提示词", provider="openai")
    
    # 验证结果
    assert response == "测试响应"
    mock_client.chat.completions.create.assert_called_once_with(
        model="gpt-4",
        messages=[{"role": "user", "content": "测试提示词"}],
        max_tokens=1000
    )

@patch('tools.llm_api.Anthropic')
def test_query_llm_anthropic(mock_anthropic):
    # 设置模拟响应
    mock_client = Mock()
    mock_anthropic.return_value = mock_client
    mock_response = Mock()
    mock_response.content = [Mock(text="测试响应")]
    mock_client.messages.create.return_value = mock_response
    
    # 调用函数
    response = query_llm("测试提示词", provider="anthropic")
    
    # 验证结果
    assert response == "测试响应"
    mock_client.messages.create.assert_called_once_with(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        messages=[{"role": "user", "content": "测试提示词"}]
    )

@patch('tools.llm_api.OpenAI')
def test_query_llm_with_image(mock_openai, tmp_path):
    # 创建测试图片
    image_path = tmp_path / "test.jpg"
    image_path.write_bytes(b"test image data")
    
    # 设置模拟响应
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_response = Mock()
    mock_response.choices = [Mock(message=Mock(content="测试响应"))]
    mock_client.chat.completions.create.return_value = mock_response
    
    # 调用函数
    response = query_llm("测试提示词", provider="openai", image_path=str(image_path))
    
    # 验证结果
    assert response == "测试响应"
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args[1]
    assert call_args["model"] == "gpt-4-vision-preview"
    assert len(call_args["messages"][0]["content"]) == 2
    assert call_args["messages"][0]["content"][0]["text"] == "测试提示词"
    assert "image_url" in call_args["messages"][0]["content"][1]

def test_query_llm_invalid_provider():
    # 验证无效提供商是否引发异常
    with pytest.raises(ValueError, match="不支持的LLM提供商: invalid"):
        query_llm("测试提示词", provider="invalid")

if __name__ == '__main__':
    unittest.main()
