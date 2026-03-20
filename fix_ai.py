import sys

f = 'bot_worker/worker/ai_service.py'
text = open(f).read()

# Fix 1: Add empty content check before record_success
old1 = """            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=4096,
            )
            _cb.record_success()"""

new1 = """            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_completion_tokens=4096,
            )

            content = response.choices[0].message.content
            if not content:
                logger.warning(f'[{model}] returned empty content, trying next model')
                continue

            _cb.record_success()"""

if old1 not in text:
    print("ERROR: old1 not found")
    sys.exit(1)
text = text.replace(old1, new1)

# Fix 2: Return content variable instead of accessing response again
old2 = '            return response.choices[0].message.content or "Извините, произошла ошибка. Попробуйте ещё раз."'
new2 = '            return content'

if old2 not in text:
    print("ERROR: old2 not found")
    sys.exit(1)
text = text.replace(old2, new2)

# Fix 3: Replace RuntimeError with graceful fallback
old3 = '    raise RuntimeError("All models failed")'
new3 = """    logger.error("All models returned empty content")
    return "Извините, произошла ошибка. Попробуйте ещё раз.\""""

if old3 not in text:
    print("ERROR: old3 not found")
    sys.exit(1)
text = text.replace(old3, new3)

open(f, 'w').write(text)
print("PATCHED OK")
