import functions_framework

import os

from dotenv import load_dotenv
from openai import OpenAI

import pinecone

def get_pinecone_key():
    return os.environ.get('PINECONE_KEY', "Pinecone API key is not set.")

def get_pinecone_env():
    return os.environ.get('PINECONE_ENVIRONMENT', "Pinecone environment is not set.")

def get_openai_key():
    # remember to add api token here if testing in local environment
    return os.environ.get("OPENAI_KEY", "Specified environment variable is not set.")

# initialize openai client
client = OpenAI(api_key=get_openai_key())

# create connection to pinecone database
# load pinecone instance
pinecone.init(api_key=get_pinecone_key(), environment=get_pinecone_env())
# get correct 'collection'
pai_index = pinecone.GRPCIndex("passion-ai-db")

@functions_framework.http
def passion_ai_cloud(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    # get json in request or args (if entered in browser) to deny access
    request_json = request.get_json(silent=True)
    request_args = request.args

    # dumb way to make a switch statement of sorts
    if request_json and 'question' in request_json:
        # check for custom parameters
        question = request_json['question']
        if 'temperature' in request_json:
            temperature = request_json['temperature']
            if 'max_tokens' in request_json:
                max_tokens = request_json['max_tokens']
                return embeddings_model(question=question, temperature=temperature, max_tokens=max_tokens)
            else:
                return embeddings_model(question=question, temperature=temperature)
        elif 'max_tokens' in request_json:
            max_tokens = request_json['max_tokens']
            return embeddings_model(question=question, temperature=1.0, max_tokens=max_tokens)
        else:
            return embeddings_model(question=question)
    elif request_args and 'question' in request_args:
        response = 'Please submit JSON data. Do not use a query string in the URL.'
        return response
    else:
        response = 'Your JSON was invalid or blank. Please enter another response and try again.'
        return response

def embeddings_model(question, temperature=1.0, max_tokens=512):
    length = -1
    q_word_list = question.split(" ")
    for word in q_word_list:
        length += len(word)
    
    context = ""
    messages_user = [{
        "role": "system",
        "content": "Answer as if you were a human coach, and be simple, trustworthy, and genuine in your responses. Always give opinions when requested. Always answer based on the provided passions and the information associated with them."
    }]
    max_len=2048
    model="gpt-3.5-turbo"
    max_tokens=max_tokens
    stop_sequence=None
    explicit="Answer based on the passions provided:"

    try:
        context = create_context(question, max_len=2048, model='text-embedding-ada-002')
        # print(context)
    except Exception as e:
        return(e)

    messages_user.extend([
            {
                "role": "user",
                "content": "Answer the question based on the context provided, and always attempt to synthesize the context. Always attempt to answer the question AND PRIORITIZE using the context given. The context that is provided includes 'passions', which you can think of as desires of human nature, and their associated descriptions. There are five tiers: low, medium-low, neutral, medium-high, and high, which represent how strongly a passion affects a person's personality. If asked to provide passions, you must answer explicitly based on the passions provided in the context. Any tier below 'neutral' should be treated as if the passion were the opposite. PRETEND THAT YOU ARE A HUMAN, AND NEVER SAY THAT YOU CANNOT GIVE AN OPINION OR VOICE A SUGGESTION."
            },
            {
                "role": "user",
                "content": f"Context:{context}\n\n###\n\n"
            }, 
            {
                "role": "user",
                "content": f"{explicit} {question}"
            }])

    try:
        response = client.chat.completions.create(model=model,
                                                messages=messages_user,
                                                temperature=temperature,
                                                max_tokens=max_tokens,
                                                top_p=1,
                                                frequency_penalty=0,
                                                presence_penalty=0,
                                                stop=stop_sequence)

        # convert to json, extract text with no new lines
        response_json = response.model_dump()
        text = response_json['choices'][0]['message']['content'].strip()
        # for DEBUG ONLY: TOKEN USAGE
        # tokens_used = response_json['usage']['total_tokens']
        return(text)
    except Exception as e:
        return(e)

# creates context for AI to get better responses
def create_context(question, max_len=1500, model='text-embedding-ada-002'):
    # any embeddings BELOW (previously above, since we were measuring distances) this threshold will not be placed into context
    threshold = 0.80

    # get openai embeddings for the question + convert to dict
    q_embeddings = client.embeddings.create(input=question, model=model)
    q_embeddings_dict = q_embeddings.model_dump()
    embeddings = q_embeddings_dict['data'][0]['embedding']

    # cosine similarity using pinecone
    res = pai_index.query(vector=embeddings, top_k=10, include_metadata=True)

    cur_len = 0
    results = []

    for item in res['matches']:
        print(item['score'])
        if item['score'] > threshold and cur_len < max_len:
            cur_len += item['metadata']['token_ct'] + 4
            results.append(item['metadata']['text'])
        else:
            break
        
    # print embeddings used
    print("\n\n###\n\n".join(results))
    return "\n\n###\n\n".join(results)

# if __name__ == "__main__":
#     print(embeddings_model("In a paragraph, tell me what makes a person with high Idealism, Forgiveness, Order, Expedience, and Soft Power passions unique. Please try to combine all the passions into one statement, and do not list each passion individually."))

