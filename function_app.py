import azure.functions as func
import logging
import requests

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