def generate_gemini_response(*args, **kwargs):
    raise NotImplementedError("Gemini direct API is deprecated. Use LangChain agent via utilities/langchain_agent.py instead.")


# import os
# from dotenv import load_dotenv
# import google.generativeai as genai
# from google.api_core import exceptions as google_exceptions
# import tenacity
# import logging

# # Load .env file
# load_dotenv()

# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     raise ValueError("GEMINI_API_KEY not found in environment variables.")

# # Configure the Gemini client
# genai.configure(api_key=GEMINI_API_KEY)

# # Retry on API/network errors or blocked content
# RETRY_EXCEPTIONS = (
#     google_exceptions.GoogleAPIError,
#     ValueError,
# )

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

# @tenacity.retry(
#     stop=tenacity.stop_after_attempt(5),
#     wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
#     retry=tenacity.retry_if_exception_type(RETRY_EXCEPTIONS),
#     before_sleep=tenacity.before_sleep_log(logger, logging.INFO),
#     reraise=True
# )
# def generate_gemini_response(prompt: str) -> str:
#     model = genai.GenerativeModel(
#         "models/gemini-1.5-flash",
#         safety_settings={
#             genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
#             genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
#             genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
#             genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
#             # genai.types.HarmCategory.MEDICAL: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
#             # genai.types.HarmCategory.HARM_CATEGORY_TOXICITY: genai.types.HarmBlockThreshold.BLOCK_NONE,
#             # genai.types.HarmCategory.HARM_CATEGORY_DEROGATORY: genai.types.HarmBlockThreshold.BLOCK_NONE,
#         }
#     )

#     logger.info("Attempting to generate Gemini response...")

#     response = model.generate_content(prompt)

#     if not response.parts:
#         logger.warning("⚠️ Gemini response was blocked due to safety concerns.")
#         raise ValueError("Gemini output was blocked by safety settings.")

#     return response.text


# # import os
# # import google.generativeai as genai
# # from dotenv import load_dotenv
# # import tenacity

# # # Load .env file
# # load_dotenv()

# # # Access the Gemini API key from environment
# # GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# # # Configure the Gemini client
# # genai.configure(api_key=GEMINI_API_KEY)

# # if not GEMINI_API_KEY:
# #     raise ValueError("GEMINI_API_KEY not found in environment variables. Please set it in your .env file.")
# # genai.configure(api_key=GEMINI_API_KEY)

# # # --- Retry Configuration ---
# # # Define the exceptions that should trigger a retry
# # RETRY_EXCEPTIONS = (
# #     genai.types.BlockedPromptException, # If prompt itself is blocked by safety
# #     genai.types.APIError,               # General API errors (network, service unavailable, etc.)
# #     tenacity.wait_exponential,          # A placeholder for connection issues, timeouts
# #                                         # (genai.types.APIError covers many network issues)
# # )

# # @tenacity.retry(
# #     stop=tenacity.stop_after_attempt(5),  # Try up to 5 times
# #     wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), # Exponential backoff: 4s, 8s, 16s, etc., max 10s
# #     retry=tenacity.retry_if_exception_type(RETRY_EXCEPTIONS),
# #     before_sleep=tenacity.before_sleep_log(genai.logging.getLogger(__name__), genai.logging.INFO),
# #     reraise=True # Re-raise the last exception if all retries fail
# # )
# # def generate_gemini_response(prompt: str) -> str:
# #     """
# #     Generates a response from Gemini, including safety settings for output and retry logic.
# #     Raises an exception if all retries fail or if the response is empty due to content blocking.
# #     """
# #     model = genai.GenerativeModel(
# #         "models/gemini-1.5-flash",
# #         safety_settings={
# #             genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
# #             genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH: genai.types.HarmBlockThreshold.BLOCK_NONE,
# #             genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: genai.types.HarmBlockThreshold.BLOCK_NONE,
# #             genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: genai.types.HarmBlockThreshold.BLOCK_NONE,
# #             genai.types.HarmCategory.HARM_CATEGORY_MEDICAL: genai.types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
# #             genai.types.HarmCategory.HARM_CATEGORY_TOXICITY: genai.types.HarmBlockThreshold.BLOCK_NONE,
# #             genai.types.HarmCategory.HARM_CATEGORY_DEROGATORY: genai.types.HarmBlockThreshold.BLOCK_NONE,
# #         }
# #     )
    
# #     print(f"Attempting to generate Gemini response (retry attempt {genai.logging.getLogger(__name__).handlers[0].formatter.log_count_for_current_attempt if hasattr(genai.logging.getLogger(__name__).handlers[0].formatter, 'log_count_for_current_attempt') else 1})...")

# #     response = model.generate_content(prompt)
    
# #     # Check if the response was blocked by safety settings (content *output* filtering)
# #     if not response.parts:
# #         print("⚠️ Gemini response was blocked due to safety concerns (output filtering).")
# #         # Instead of returning empty string, raise a specific exception
# #         # so `generate_daily_insight` can handle it clearly.
# #         raise ValueError("Gemini output was blocked by safety settings.")
        
# #     return response.text

# # # def generate_gemini_response(prompt: str) -> str:
# # #     model = genai.GenerativeModel("models/gemini-1.5-flash")  # Updated model name
# # #     response = model.generate_content(prompt)
# # #     return response.text
