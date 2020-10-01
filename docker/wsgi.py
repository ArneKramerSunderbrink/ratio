from ratio import create_app

app = create_app()
app.config['SECRET_KEY'] = b'O\xf3$\xdbM\x05\xa7\xa8RL\xe1\x13\x05P\x036'

if __name__ == "__main__":
    app.run()
