import azure.functions as func
import json
import os
from azure.iot.hub import IoTHubRegistryManager

app = func.FunctionApp()

# Diese ID muss exakt mit dem Verbindungsstring in deinen App Settings übereinstimmen
CONNECTION_STRING = os.environ.get("IOTHUB_CONNECTION_STRING")

@app.route(route="manageContainer", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def manage_container(req: func.HttpRequest) -> func.HttpResponse:
    try:
        req_body = req.get_json()
        device_id = req_body.get('device_id') # z.B. "TurboPi"
        module_id = req_body.get('module_id') # Name deines Containers
        action = req_body.get('action')       # "start" oder "stop"

        if not all([device_id, module_id, action]):
            return func.HttpResponse("Parameter fehlen (device_id, module_id, action)", status_code=400)

        # Status übersetzen
        target_status = "running" if action.lower() == "start" else "stopped"

        # Verbindung zum IoT Hub herstellen
        registry_manager = IoTHubRegistryManager(CONNECTION_STRING)

        # Den "Desired State" des Edge Agents patchen
        # Der $edgeAgent ist das System-Modul, das Docker-Befehle ausführt
        twin_patch = {
            "properties": {
                "desired": {
                    "modules": {
                        module_id: {
                            "status": target_status
                        }
                    }
                }
            }
        }

        # Update senden
        registry_manager.update_module_twin(device_id, "$edgeAgent", twin_patch, "*")

        return func.HttpResponse(
            json.dumps({"status": "success", "message": f"Modul {module_id} auf {target_status} gesetzt"}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(f"Fehler: {str(e)}", status_code=500)