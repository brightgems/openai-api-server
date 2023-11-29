import tiktoken

# gpt-4, gpt-3.5-turbo, text-embedding-ada-002
ENCODER = tiktoken.get_encoding("cl100k_base")


def get_model_token_limit(model: str) -> int:
    """get max limit of token by model"""
    if model == 'gpt-4-1106-preview':
        return 4000
    elif model == 'gtp-4':
        return 8000
    elif model.find('16k') > 0:
        return 16000
    elif model.find('32k') > 0:
        return 32000
    else:
        return 4000


def get_max_tokens(model: str, prompt: str, max_expect: int = 4000) -> int:
    """
    Get the max tokens for a complete message
    """
    token_limit = get_model_token_limit(model)
    max_tokens = token_limit - len(ENCODER.encode(prompt))
    if max_tokens < 0:
        return 512
    elif max_tokens > max_expect:
        return max_expect
    else:
        return max_tokens


class ChatgptAPIException(Exception):
    """ChatGPT API error
    """
    pass
