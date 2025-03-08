from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Função de login
def login(login, senha):
    url_login = "https://edusp-api.ip.tv/registration/edusp"
    headers = {
        'x-api-realm': 'edusp',
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json',
        'x-api-platform': 'webclient'
    }
    body = {
        'realm': 'edusp',
        'platform': 'webclient',
        'id': login,
        'password': senha
    }

    response = requests.post(url_login, headers=headers, json=body)

    if response.status_code == 200:
        data = response.json()
        if "nick" in data and "auth_token" in data:
            return {"success": True, "nick": data["nick"], "auth_token": data["auth_token"]}
    
    return {"success": False, "message": "Usuário ou senha inválidos."}

@app.route('/login', methods=['POST'])
def api_login():
    data = request.json
    login_result = login(data['login'], data['senha'])
    return jsonify(login_result)

# Função para pegar rooms e IDs dos grupos
def fetch_rooms_and_group_ids(authToken):
    url_room = "https://edusp-api.ip.tv/room/user?list_all=true&with_cards=true"
    headers = {'x-api-key': authToken, 'Accept': 'application/json'}
    response = requests.get(url_room, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if 'rooms' in data:
            rooms = [room_data['name'] for room_data in data['rooms'] if 'name' in room_data]
            group_ids = {str(group['id']) for room in data.get('rooms', []) for group in room.get('group_categories', []) if 'id' in group}
            print(f"🏠 Rooms encontradas: {rooms}")
            print(f"🔑 IDs de grupos filtrados: {group_ids}")
            return rooms, list(group_ids)
        else:
            print("❌ Nenhuma 'room' encontrada na resposta.")
            return [], []
    
    print(f"❌ Erro ao obter os dados das rooms. Status: {response.status_code}")
    print(f"Detalhes do erro: {response.text}")
    return [], []

# Função para pegar as tarefas
def get_tasks(authToken, rooms):
    url = "https://edusp-api.ip.tv/tms/task/todo"
    
    params = {
        "expired_only": "false",  # Sempre falso
        "limit": "100",
        "offset": "0",
        "is_exam": "false",
        "with_answer": "true",
        "is_essay": "false",
        "publication_target": rooms,  # Usando vírgulas para múltiplos valores
        "answer_statuses": "pending"  # Passando apenas 'pending'
    }
    
    headers = {
        'accept': 'application/json',
        'x-api-key': authToken
    }

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()

        if isinstance(data, list):
            print("✅ Requisição bem-sucedida!")
            tasks = [{"id": task.get("id"), "title": task.get("title"), "questions": task.get("questions", [])} for task in data]
            print(f"📜 Tarefas encontradas: {len(tasks)}")
            return tasks
        else:
            print("❌ A resposta da API não contém uma lista válida de tarefas.")
            print(f"Resposta da API: {response.text}")
            return []
    
    print(f"❌ Erro na requisição. Código de status: {response.status_code}")
    print("Detalhes do erro:", response.text)
    return []


def apply_task(authToken, task_id):
    url = f"https://edusp-api.ip.tv/tms/task/{task_id}/apply?preview_mode=false"
    
    headers = {
        'accept': 'application/json',
        'x-api-key': authToken
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print(f"🔍 Buscando tarefa {task_id}...")
        data = response.json()
        
        if 'questions' in data:
            questions = []
            for question in data['questions']:
                question_id = question.get('id', 'ID não encontrado')
                question_type = question.get('type', 'Tipo não encontrado')

                # Imprimindo o ID e o tipo da questão
                print(f"🔑 ID da Questão: {question_id}")
                print(f"✨ Tipo da questão: {question_type}")
                
                # Ignorar questões do tipo 'info'
                if question_type == 'info':
                    print(f"❌ Ignorando questão do tipo 'info' (ID: {question_id}).")
                    continue
                
                # Verificando se a questão é do tipo 'fill-words' antes de procurar os itens
                if question_type == 'fill-words':
                    items = []
                    if 'options' in question and question['options'] is not None:
                        options = question['options']
                        items = options.get('items', [])
                        phrase = options.get('phrase', [])
                        print(f"🌱 Itens encontrados para a questão (ID da questão fill-words: {question_id}): {items}")
                        print(f"📜 Frase encontrada: {phrase}")

                        # Adiciona os itens e a frase relacionados à questão 'fill-words'
                        questions.append({
                            'question_id': question_id,
                            'type': question_type,
                            'items': items,  # Associando os itens à questão 'fill-words'
                            'options': phrase  # Passando a frase para ser usada na resposta
                        })
                    else:
                        print("❗ Nenhum item encontrado para a questão fill-words.")
                
                # Adicionando suporte para questões do tipo 'order-sentences'
                elif question_type == 'order-sentences':
                    sentences = question.get('options', {}).get('sentences', [])
                    print(f"📜 Sentenças encontradas para a questão (ID da questão order-sentences: {question_id}): {sentences}")

                    # Adiciona as sentenças à lista de perguntas
                    questions.append({
                        'question_id': question_id,
                        'type': question_type,
                        'sentences': sentences  # Associando as sentenças à questão 'order-sentences'
                    })
                
                else:
                    # Para outros tipos de questão, não procuramos por 'items'
                    print(f"❗ Ignorando busca por itens para a questão do tipo '{question_type}' (ID: {question_id}).")
                    questions.append({
                        'question_id': question_id,
                        'type': question_type,
                        'items': []  # Adiciona uma lista vazia para manter a estrutura
                    })
                
            return questions
    else:
        print(f"❌ Erro ao buscar a tarefa {task_id}. Status: {response.status_code}")
        print(f"Detalhes do erro: {response.text}")
        return None

# Função para enviar a resposta
def send_answer(authToken, task_id, questions, room):
    url = f"https://edusp-api.ip.tv/tms/task/{task_id}/answer"
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "x-api-key": authToken,
    }
    
    # Formatação das respostas para a API
    answers = {}
    
    for question in questions:
        question_id = question['question_id']
        question_type = question['type']
        
        print(f"🔑 ID da Questão: {question_id}")
        print(f"✨ Tipo da questão: {question_type}")
        
        if question_type == 'single':
            answer_id = 0  # Considerar o ID da resposta como 0
            answers[question_id] = {
                "score": 0,  # Score fixo como 0
                "question_id": question_id,
                "question_type": "single",
                "question_invalid": False,
                "answer": [answer_id]
            }
            print(f"📬 Resposta (single) enviada para a questão {question_id} com sucesso: {answers[question_id]}")
        
        elif question_type == 'multi':
            answers[question_id] = {
                "score": 0,  # Score fixo como 0
                "question_id": question_id,
                "question_type": "multi",
                "question_invalid": False,
                "answer": {0: True, 1: False, 2: True, 3: False, 4: False}  # Exemplo de resposta
            }
            print(f"📬 Resposta (multi) enviada para a questão {question_id} com sucesso: {answers[question_id]}")
        
        elif question_type == 'fill-words':
            items = question.get('items', [])
            options = question.get('options', [])
            
            fill_in_text = []  # Para armazenar a resposta formatada
            used_items = set()  # Para rastrear itens já usados
            
            for part in options:
                if part.get('type') == 'text':
                    # Adiciona o texto diretamente
                    fill_in_text.append({
                        "type": "text",
                        "value": part['value']
                    })
                elif part.get('type') == 'select':
                    # Preencher o campo select com um item não repetido
                    available_items = [item for item in items if item not in used_items]
                    if available_items:
                        selected_item = available_items[0]  # Seleciona o primeiro item disponível
                        fill_in_text.append({
                            "type": "select",
                            "value": selected_item
                        })
                        used_items.add(selected_item)  # Marca o item como usado
                    else:
                        fill_in_text.append({
                            "type": "select",
                            "value": ""  # Se não houver mais itens, deixar vazio
                        })
            
            # Montando a resposta no formato desejado
            answers[question_id] = {
                "score": 0,  # Score fixo como 0
                "question_id": question_id,
                "question_type": "fill-words",
                "question_invalid": False,
                "options": fill_in_text  # Resposta gerada no formato correto
            }
            print(f"📬 Resposta (fill-words) enviada para a questão {question_id} com sucesso: {answers[question_id]}")
        
        elif question_type == 'true-false':
            # Exemplo de resposta para true-false
            answers[question_id] = {
                "score": 0,  # Score fixo como 0
                "question_id": question_id,
                "question_type": "true-false",
                "question_invalid": False,
                "answer": {0: True, 1: False, 2: True, 3: False}  # Exemplo de respostas
            }
            print(f"📬 Resposta (true-false) enviada para a questão {question_id} com sucesso: {answers[question_id]}")
        
        else:
            print(f"❌ Tipo de questão não reconhecido: {question_type}")
            answers[question_id] = {"text": "Resposta para esse tipo de questão"}
    
    # Imprimir o payload de respostas para debug
    print(f"📝 Respostas geradas: {json.dumps(answers, indent=2)}")
    
    payload = {
        "task_id": task_id,
        "answers": answers,
        "executed_on": room,
        "accessed_on": "room",
    }
    
    # Imprimir o payload completo antes de enviar
    print(f"📦 Payload a ser enviado: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        print("✅ Resposta enviada com sucesso!")
        print(f"Resposta enviada: {json.dumps(payload, indent=2)}")  # Mostra a resposta enviada
    else:
        print("❌ Erro ao enviar a resposta:")
        print(f"Status: {response.status_code}")
        print(f"Detalhes: {response.text}")

# Função principal que orquestra o processo
def main():
    userNick, authToken = login()
    
    rooms, group_ids = fetch_rooms_and_group_ids(authToken)
    
    if not rooms:
        print("❌ Não foi possível encontrar rooms válidas.")
        return
    
    tasks = get_tasks(authToken, rooms)
    
    if tasks:
        for task in tasks:  # Itera sobre todas as tarefas encontradas
            task_id = task['id']
            print(f"🔑 Buscando informações da tarefa {task_id}...")
            questions = apply_task(authToken, task_id)
            
            if questions:
                send_answer(authToken, task_id, questions, rooms[0])  # Passando room como parâmetro
    else:
        print("❌ Nenhuma tarefa encontrada.")

if __name__ == "__main__":
    app.run(debug=True)