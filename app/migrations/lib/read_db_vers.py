from app import db, create_app


def get_version(commit=True):
    app = create_app()
    with app.app_context():
        connection = db.connect
        query = f"""SELECT version from db_version;"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchone()
            if commit:
                connection.commit()
                if cursor:
                    cursor.close()
            return results[0]
        except:
            return None
