# handled chatting with davinci v3
"""
    def ask_question_v3(self,
                        df,
                        question="",
                        model="text-davinci-003",
                        max_len=1024,
                        size="ada",
                        max_tokens=256,
                        stop_sequence=None):
        context = self.create_context(question, df, max_len, size=size)

        temperature = 0.9
        print(f"Temperature: {temperature}\n")
        try:
            response = openai.Completion.create(
            prompt=
            f"Answer the question based on the context below, and always attempt to synthesize the context into a unique personality. Always attempt to answer the question AND PRIORITIZE using the context, however you may draw from prior knowledge as well. There are five tiers: low, medium-low, neutral, medium-high, and high, which represent how strongly a passion affects a person's personality. Any tier below 'neutral' should be treated as if the passion were the opposite.\n\nContext: {context}\n\n---\n\nQuestion: {question}\nAnswer:",
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence)
            return (response["choices"][0]["text"].strip())

            response = openai.Completion.create(
            prompt=
            f"Answer the question based on the current knowledge that you have.\n\nQuestion: {question}\nAnswer:",
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence)
            print(response["choices"][0]["text"].strip())
            # return response["choices"][0]["text"].strip()
        except Exception as e:
            print(e)
            return ""

        return ""


        messages = [{
        "role":
        "system",
        "content":
        "Answer as a chatbot, and be simple, trustworthy, and genuine in  your responses."
        }, {
        "role":
        "user",
        "content":
        "Answer the question based on the information provided, and always attempt to synthesize the information into a unique personality. Always attempt to answer the question AND PRIORITIZE using the information given, however you may draw from prior knowledge as well. There are five tiers: low, medium-low, neutral, medium-high, and high, which represent how strongly a passion affects a person's personality. Any tier below 'neutral' should be treated as if the passion were the opposite."
        }]
        context = None


    def ask_question_v35(self,
                     df,
                     question="",
                     model="gpt-3.5-turbo",
                     max_len=1024,
                     size="ada",
                     max_tokens=512,
                     stop_sequence=None):
        global context
        global messages
        if context == None:
            context = self.create_context(question, df, max_len, size=size)
            messages.extend([{
            "role": "assistant",
            "content": context
            }, {
            "role": "user",
            "content": question
            }])
        else:
            messages.append({"role": "user", "content": question})
        temperature = 1.0

        print(f"Temperature: {temperature}\n")
        print(messages)
        try:
            response = openai.ChatCompletion.create(model=model,
                                                    messages=messages,
                                                    temperature=temperature,
                                                    max_tokens=max_tokens,
                                                    top_p=1,
                                                    frequency_penalty=0,
                                                    presence_penalty=0,
                                                    stop=stop_sequence)

            # convert to json, extract text with no new lines
            response_json = json.loads(str((response)))
            text = response_json['choices'][0]['message']['content'].strip()
            return text
        except Exception as e:
            print(e)
            return ""

        return ""
"""