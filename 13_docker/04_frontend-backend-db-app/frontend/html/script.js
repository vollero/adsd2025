// Assicurati che l'URL del backend corrisponda a come esponi il backend
// Se docker-compose mappa la porta 5000 del backend alla 5001 dell'host:
const BACKEND_URL = 'http://192.168.71.128:5001/api'; // Modifica la porta se necessario

async function fetchItems() {
    const itemsList = document.getElementById('items-list');
    const errorMessage = document.getElementById('error-message');
    itemsList.innerHTML = '<li>Caricamento...</li>'; // Messaggio di caricamento
    errorMessage.textContent = '';

    try {
        const response = await fetch(`${BACKEND_URL}/items`);
        if (!response.ok) {
            throw new Error(`Errore HTTP: ${response.status} - ${response.statusText}`);
        }
        const items = await response.json();
        
        itemsList.innerHTML = ''; // Pulisci la lista
        if (items.length === 0) {
            itemsList.innerHTML = '<li>Nessun item trovato.</li>';
        } else {
            items.forEach(item => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `<span class="item-name">${item.name}</span> (ID: ${item.id}) <br><span class="item-date">Creato: ${item.created_at}</span>`;
                itemsList.appendChild(listItem);
            });
        }
    } catch (error) {
        console.error('Errore nel fetch degli items:', error);
        itemsList.innerHTML = '<li>Errore nel caricare gli items.</li>';
        errorMessage.textContent = `Impossibile caricare gli items: ${error.message}. Assicurati che il backend sia in esecuzione e raggiungibile.`;
    }
}

async function addItem() {
    const itemNameInput = document.getElementById('itemName');
    const itemName = itemNameInput.value.trim();
    const errorMessage = document.getElementById('error-message');
    errorMessage.textContent = '';

    if (!itemName) {
        errorMessage.textContent = 'Il nome dell\'item non può essere vuoto.';
        return;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/items`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: itemName }),
        });

        if (!response.ok) {
             const errorData = await response.json().catch(() => ({ detail: response.statusText })); // Prova a leggere il JSON di errore
             throw new Error(`Errore HTTP: ${response.status} - ${errorData.error || errorData.detail || response.statusText}`);
        }
        
        // const newItem = await response.json(); // Non necessario se non usiamo newItem
        await response.json(); 
        itemNameInput.value = ''; // Pulisci l'input
        fetchItems(); // Ricarica la lista degli items
    } catch (error) {
        console.error('Errore nell\'aggiungere l\'item:', error);
        errorMessage.textContent = `Impossibile aggiungere l'item: ${error.message}`;
    }
}

// Carica gli items quando la pagina è pronta
document.addEventListener('DOMContentLoaded', fetchItems);
