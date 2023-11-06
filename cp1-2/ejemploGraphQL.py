#Paso 1 Importación de librerías
from flask import Flask,request,jsonify
from flask_graphql import GraphQLView
import graphene

app = Flask(__name__)

#Paso 2 Creación de equemas graphQL y rutas
class Query(graphene.ObjectType):
    billy = graphene.String(description='A typical hello world')
    def resolve_billy(self, info):
        return 'World'
    hello = graphene.String(description='A typical hello world')
    def resolve_hello(self, info):
        return 'Hello World'

schema = graphene.Schema(query=Query)  
#CURL -X POST -H "Content-Type:application/json" -d '{"query":"{billy}"}'  http://localhost:5000/graphql
#CURL -X POST -H "Content-Type:application/json" -d '{"query":"{hello}"}'  http://localhost:5000/graphql

#Paso 3 Creación de funciones para resolver las consultas
# @app.route('/graphql',methods=['POST'])
# def graphql():
#     data = request.get_json()
#     result = schema.execute(data['query'])
#     return jsonify(result.data)

app.add_url_rule('/graphql', 
                 view_func=GraphQLView.as_view('graphql', 
                                           schema=schema, graphiql=True))

#Paso 4 Ejecución del servidor
if __name__ == '__main__':
    app.run(debug=True)