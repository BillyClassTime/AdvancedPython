from flask import Flask,request,jsonify
from flask_graphql import GraphQLView
import graphene

app = Flask(__name__)

class Query(graphene.ObjectType):
    mensaje = graphene.String()
    def resolve_mensaje(self, info):
        #conectarnos a la base de datos
        return 'Respuesta desde el servidor con el mensaje'
    
schema = graphene.Schema(query=Query)

# @app.route('/graphql', methods=['POST'])
# def graphql():
#     data = request.get_json()
#     result =  schema.execute(data['query'])
#     #return GraphQLView.as_view(graphiql=True, schema=schema, context={'request': request})()
#     return jsonify(result.data)

app.add_url_rule('/graphql', 
                 view_func=GraphQLView.as_view('graphql', 
                                               schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True, port=8000)