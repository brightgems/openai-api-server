import tiktoken

ENCODER = tiktoken.get_encoding("gpt2")


def get_model_token_limit(model: str) -> int:
    """get max limit of token by model"""
    if model.startswith('gtp-4'):
        return 8000
    elif model.startswith('gpt-4-32k'):
        return 32000
    else:
        return 4000


def get_max_tokens(model: str, prompt: str, max_expect: int = 4000) -> int:
    """
    Get the max tokens for a complete message
    """
    token_limit = get_model_token_limit(model)
    max_tokens = token_limit - len(ENCODER.encode(prompt))
    if max_tokens < 0 or max_tokens > max_expect:
        return max_expect
    else:
        return max_tokens


class ChatgptAPIException(Exception):
    """ChatGPT API error
    """
    pass
