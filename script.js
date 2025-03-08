// Alterna entre o modo claro e escuro
document.getElementById('toggle-theme').addEventListener('click', () => {
    document.body.classList.toggle('light-mode');
});

// Função para limpar o campo de texto (usuário)
document.querySelectorAll('.clear-icon').forEach(icon => {
    icon.addEventListener('click', function(event) {
        // Evitar que o clique no ícone de limpar afete o comportamento do ícone da senha
        if (event.target.id !== 'toggle-password') {
            const inputField = this.closest('.input-wrapper').querySelector('input'); // Encontrar o campo de texto
            inputField.value = ''; // Limpar o valor do campo de texto
        }
        event.stopPropagation(); // Impede que o clique afete outros elementos
    });
});

// Função para alternar a visibilidade da senha
const togglePassword = document.getElementById('toggle-password'); // Usando ID específico
const passwordInput = document.getElementById('password');

togglePassword.addEventListener('click', function(event) {
    // Impede que o clique no ícone de olho afete o comportamento de limpar o campo de usuário
    event.stopPropagation();  // Impede que o clique no ícone de olho afete outros elementos

    // Alterna entre mostrar e ocultar a senha
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text'; // Torna a senha visível
        this.src = 'eye-open.png'; // Imagem de olho aberto
    } else {
        passwordInput.type = 'password'; // Torna a senha oculta
        this.src = 'eye-close.png'; // Imagem de olho fechado
    }
});

document.getElementById('login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    const response = await fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ login: username, senha: password })
    });

    const result = await response.json();
    showMessage(result);
});

function showMessage(result) {
    const messageCard = document.getElementById('message-card');
    messageCard.innerText = result.success ? 
        `Login bem-sucedido! Bem-vindo, ${result.nick}` : 
        result.message;

    messageCard.classList.add('show');
    setTimeout(() => {
        messageCard.classList.remove('show');
    }, 3000); // Duração da mensagem
}
