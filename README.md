Create a folder `./docs` to organize things, put the PDFs in ./docs/, and run:

    docker compose run --rm app bash -c "python app.py docs/Title_20.pdf IN TITLE > docs/Title_20.md"

for now, tempfiles are generated in a timestamped folder under ./tmp/ for examination and debugging
