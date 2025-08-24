import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_CREDENTIALS_PATH

class FirebaseDB:
    def __init__(self):
        """
        Inicializa la conexión a Firebase Firestore.
        """
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def guardar_documento(self, coleccion, documento_id, data):
        """
        Guarda un documento en la colección especificada.
        Si el documento existe, lo sobrescribe.
        """
        try:
            self.db.collection(coleccion).document(documento_id).set(data)
            print(f"✅ Documento guardado en {coleccion}/{documento_id}")
        except Exception as e:
            print(f"❌ Error al guardar documento: {e}")

    def agregar_documento(self, coleccion, data):
        """
        Agrega un documento a una colección (ID autogenerado).
        Retorna el ID del documento creado.
        """
        try:
            doc_ref = self.db.collection(coleccion).add(data)
            print(f"✅ Documento agregado en {coleccion} con ID {doc_ref[1].id}")
            return doc_ref[1].id
        except Exception as e:
            print(f"❌ Error al agregar documento: {e}")
            return None

    def obtener_documento(self, coleccion, documento_id):
        """
        Obtiene un documento por ID.
        """
        try:
            doc = self.db.collection(coleccion).document(documento_id).get()
            if doc.exists:
                return doc.to_dict()
            else:
                print(f"⚠️ Documento {documento_id} no encontrado en {coleccion}")
                return None
        except Exception as e:
            print(f"❌ Error al obtener documento: {e}")
            return None

    def obtener_coleccion(self, coleccion):
        """
        Obtiene todos los documentos de una colección.
        """
        try:
            docs = self.db.collection(coleccion).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"❌ Error al obtener colección: {e}")
            return []
