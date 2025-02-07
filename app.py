from dotenv import load_dotenv
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.language.conversations import ConversationAnalysisClient
import streamlit as st
from PIL import Image
import base64
from io import BytesIO

def main():
    try:
        # Configuración de la aplicación Streamlit
        st.set_page_config(page_title='Pedidos Rapidisimos')

        logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        image = Image.open(logo_path)
        st.markdown("""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{0}" alt="Logo" style="width:300px;"><br>
                <h1 style="font-size: 48px;">Pedidos Rapidisimos</h1>
            </div>
        """.format(get_image_as_base64(image)), unsafe_allow_html=True)
        
        # Obtener configuración
        load_dotenv()
        ls_prediction_endpoint = os.getenv('LS_CONVERSATIONS_ENDPOINT')
        ls_prediction_key = os.getenv('LS_CONVERSATIONS_KEY')

        # Obtener entrada del usuario (a través de la interfaz de Streamlit)
        userText = st.text_input("Ingrese su consulta:", "")
        
        if userText and userText.lower() != 'quit':
            # Crear cliente para el modelo de lenguaje
            client = ConversationAnalysisClient(
                ls_prediction_endpoint, AzureKeyCredential(ls_prediction_key))
            
            # Llamar al modelo en Azure
            cls_project = 'PedidosRapidisimos'
            deployment_slot = 'prueba2'

            with client:
                query = userText
                result = client.analyze_conversation(
                    task={
                        "kind": "Conversation",
                        "analysisInput": {
                            "conversationItem": {
                                "participantId": "1",
                                "id": "1",
                                "modality": "text",
                                "language": "es",
                                "text": query
                            },
                            "isLoggingEnabled": False
                        },
                        "parameters": {
                            "projectName": cls_project,
                            "deploymentName": deployment_slot,
                            "verbose": True
                        }
                    }
                )

            top_intent = result["result"]["prediction"]["topIntent"]
            entities = result["result"]["prediction"]["entities"] or "ninguna"

            st.info(f"**Intent detectado:** {top_intent}")
            if entities == "ninguna":
                st.info("**Entidades detectadas:** ninguna", icon="ℹ️")
            else:
                entidad_texto = "**Entidades detectadas:**\n\n"
                for entity in entities:
                    entidad_texto += f"Categoría: {entity['category']} - Texto: {entity['text']} - Confianza: {entity['confidenceScore']}\n\n"
                st.info(entidad_texto, icon="ℹ️")
            
            # Aplicar la acción según la intención detectada
            if top_intent == 'OrdenarComida':
                producto = next((e['text'] for e in entities if e['category'] == 'producto'), 'algo')
                st.success(f"Pedido confirmado: {producto}. ¡Gracias por su orden!")

            elif top_intent == 'EstadoPedido':
                num_pedido = next((e['text'] for e in entities if e['category'] == 'número_pedido'), 'desconocido')
                st.success(f"Buscando estado del pedido {num_pedido}...")

            elif top_intent == 'CancelarPedido':
                num_pedido = next((e['text'] for e in entities if e['category'] == 'número_pedido'), 'desconocido')
                st.success(f"Intentando cancelar el pedido {num_pedido}...")

            elif top_intent == 'VerMenu':
                categoria = next((e['text'] for e in entities if e['category'] == 'categoría'), 'todo')
                st.success(f"Mostrando menú de {categoria}...")

            elif top_intent == 'HorarioAtencion':
                dia = next((e['text'] for e in entities if e['category'] == 'día'), 'general')
                st.success(f"El horario para {dia} es de 9:00 a 22:00.")
            
            else:
                st.success('Lo siento, no entendí la solicitud. Intente de nuevo.')

    except Exception as ex:
        st.error(ex)

def get_image_as_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

if __name__ == "__main__":
    main()
