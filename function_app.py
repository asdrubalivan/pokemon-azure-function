import azure.functions as func
import logging
import requests
import json
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="query_pokemon")
def query_pokemon(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing request for Pokémon query.')

    # Retrieve "pokemon" from query string or request body; default to 'pikachu'
    pokemon = req.params.get('pokemon')
    if not pokemon:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}
        pokemon = req_body.get('pokemon', 'pikachu')

    # Call the PokéAPI for the provided Pokémon (ensure lowercase)
    pokeapi_url = f'https://pokeapi.co/api/v2/pokemon/{pokemon.lower()}'
    response = requests.get(pokeapi_url)  # Alternatively, use 'requests.get' if imported separately

    if response.status_code == 200:
        data = response.json()
        name = data.get('name', 'unknown').capitalize()
        height = data.get('height', 'unknown')
        weight = data.get('weight', 'unknown')
        abilities = ', '.join(a['ability']['name'] for a in data.get('abilities', []))

        result = (f"Name: {name}\n"
                  f"Height: {height}\n"
                  f"Weight: {weight}\n"
                  f"Abilities: {abilities}")
        return func.HttpResponse(result, status_code=200)
    else:
        return func.HttpResponse(
            f"Error: Pokémon '{pokemon}' not found.",
            status_code=404
        )

@app.function_name(name="QueueProducer")
@app.route(route="produce", methods=["POST"])
@app.queue_output(arg_name="outQueueItem", queue_name="myqueue", connection="AzureWebJobsStorage")
def queue_producer(req: func.HttpRequest, outQueueItem: func.Out[str]) -> str:
    logging.info("QueueProducer received a request.")
    try:
        # Parse the JSON payload from the HTTP request
        req_body = req.get_json()
    except ValueError:
        return json.dumps({"error": "Invalid JSON payload."})
    
    # Optionally, process or validate the JSON data here.
    # For demonstration, we pass the entire JSON object to the queue.
    message = json.dumps(req_body)  # Serialize the JSON dictionary into a string
    outQueueItem.set(message)  # Send the message to the queue
    return message  # This string is sent to the queue

# Queue-triggered function that reads and logs the JSON message from the queue
@app.function_name(name="QueueConsumer")
@app.queue_trigger(arg_name="msg", queue_name="myqueue", connection="AzureWebJobsStorage")
def queue_consumer(msg: func.QueueMessage) -> None:
    message_body = msg.get_body().decode("utf-8")
    try:
        # Convert the JSON string back to a dictionary
        message_json = json.loads(message_body)
        logging.info(f"QueueConsumer processed JSON message: {message_json}")
    except json.JSONDecodeError:
        logging.error("QueueConsumer received invalid JSON.")