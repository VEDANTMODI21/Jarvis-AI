from gpt4all import GPT4All

model = GPT4All("mistral-7b")  # Or another model you downloaded

while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break
    response = model.chat(user_input)
    print("AI:", response)
