from firstblog import app,db,User

user_1 = User(username = 'Charan', email='abc@gmail.com',password='password')
with app.app_context():
    db.session.add(user_1)
    print('user added')
db.commit()