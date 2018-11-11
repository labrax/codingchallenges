from app import app, db
from app.models import UserInformation


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'UserInformation': UserInformation}


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True, host='0.0.0.0')
    
