// Manejo del formulario
document.getElementById('recipeForm').addEventListener('submit', function(e) {
    e.preventDefault();
    generateRecipe();
});

// Función para generar la receta
function generateRecipe() {
    const formData = new FormData(document.getElementById('recipeForm'));
    const selections = {};
    
    // Recopilar todas las selecciones
    const fields = [
        'tiempo_comida', 'tipo_cocina', 'nivel_saludable', 'cantidad_personas',
        'presupuesto', 'tiempo_disponible', 'intensidad_sabor', 'tipo_ocasion',
        'nivel_habilidad'
    ];
    
    // Campos de radio (selección individual)
    fields.forEach(field => {
        const value = formData.get(field);
        if (value && value !== 'Cualquiera') {
            selections[field] = value;
        }
    });
    
    // Campos de checkbox (selección múltiple)
    const checkboxFields = [
        'metodo_preparacion', 'tipo_proteina', 'base_plato', 
        'preferencias', 'tipo_plato'
    ];
    
    checkboxFields.forEach(field => {
        const values = formData.getAll(field);
        const filtered = values.filter(v => v !== 'Cualquiera');
        if (filtered.length > 0) {
            selections[field] = filtered;
        }
    });
    
    // Mostrar resumen
    displaySummary(selections);
    
    // Generar prompt
    const prompt = generateChatGPTPrompt(selections);
    document.getElementById('chatgptPrompt').value = prompt;
    
    // Mostrar sección de resultados
    document.getElementById('resultSection').classList.remove('hidden');
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });
    
    // Resetear rating
    resetRating();
}

// Función para mostrar el resumen
function displaySummary(selections) {
    const summaryDiv = document.getElementById('summary');
    let html = '';
    
    const labels = {
        tiempo_comida: '⏰ Tiempo de comida',
        tipo_cocina: '🌍 Tipo de cocina',
        nivel_saludable: '🥗 Nivel de saludable',
        cantidad_personas: '👥 Cantidad de personas',
        presupuesto: '💰 Presupuesto',
        metodo_preparacion: '🔥 Método de preparación',
        tipo_proteina: '🍖 Tipo de proteína',
        base_plato: '🍝 Base del plato',
        tiempo_disponible: '⏱️ Tiempo disponible',
        preferencias: '🚫 Preferencias o restricciones',
        intensidad_sabor: '🌶️ Intensidad de sabor',
        tipo_ocasion: '🎉 Tipo de ocasión',
        tipo_plato: '🍴 Tipo de plato',
        nivel_habilidad: '👨‍🍳 Nivel de habilidad culinaria'
    };
    
    for (const [key, value] of Object.entries(selections)) {
        const label = labels[key] || key;
        const displayValue = Array.isArray(value) ? value.join(', ') : value;
        html += `<div class="summary-item">
            <span class="summary-label">${label}:</span>
            <span>${displayValue}</span>
        </div>`;
    }
    
    summaryDiv.innerHTML = html || '<p>No se han seleccionado preferencias específicas.</p>';
}

// Función para generar el prompt de ChatGPT
function generateChatGPTPrompt(selections) {
    let prompt = "Crea una receta de cocina personalizada con las siguientes especificaciones:\n\n";
    
    const descriptions = {
        tiempo_comida: (v) => `Tiempo de comida: ${v}`,
        tipo_cocina: (v) => `Tipo de cocina: ${v}`,
        nivel_saludable: (v) => `Nivel de saludable: ${v}`,
        cantidad_personas: (v) => `Para ${v} persona(s)`,
        presupuesto: (v) => `Presupuesto: ${v}`,
        metodo_preparacion: (v) => `Método(s) de preparación: ${Array.isArray(v) ? v.join(', ') : v}`,
        tipo_proteina: (v) => `Tipo(s) de proteína: ${Array.isArray(v) ? v.join(', ') : v}`,
        base_plato: (v) => `Base del plato: ${Array.isArray(v) ? v.join(', ') : v}`,
        tiempo_disponible: (v) => `Tiempo disponible: ${v}`,
        preferencias: (v) => `Preferencias/restricciones: ${Array.isArray(v) ? v.join(', ') : v}`,
        intensidad_sabor: (v) => `Intensidad de sabor: ${v}`,
        tipo_ocasion: (v) => `Tipo de ocasión: ${v}`,
        tipo_plato: (v) => `Tipo de plato: ${Array.isArray(v) ? v.join(', ') : v}`,
        nivel_habilidad: (v) => `Nivel de habilidad culinaria: ${v}`
    };
    
    for (const [key, value] of Object.entries(selections)) {
        if (descriptions[key]) {
            prompt += `- ${descriptions[key](value)}\n`;
        }
    }
    
    prompt += `\nPor favor, proporciona una receta completa que incluya:
1. Nombre de la receta
2. Lista de ingredientes con cantidades específicas
3. Instrucciones paso a paso detalladas
4. Tiempo estimado de preparación y cocción
5. Información nutricional aproximada (mencionar que tan saludable es la receta)
6. Consejos o variaciones (opcional)

IMPORTANTE: Tomar en cuenta el archivo de products_20251118_010114_productos_comestibles.txt para obtener crear esta receta. Este archivo contiene una lista completa de productos comestibles disponibles con sus precios en Quetzales (Q).

Al final de la receta, DEBES incluir:
- Productos necesarios a comprar (basándote en los productos disponibles en el archivo mencionado)
- Presupuesto por producto (precio en Quetzales Q de cada producto según el archivo)
- Presupuesto detallado y total (suma de todos los productos necesarios)

Asegúrate de que la receta sea práctica, deliciosa y se ajuste a todas las especificaciones mencionadas. Los productos deben ser seleccionados del archivo de productos comestibles disponibles.`;
    
    return prompt;
}

// Función para copiar al portapapeles
document.getElementById('copyBtn').addEventListener('click', async function() {
    const promptText = document.getElementById('chatgptPrompt').value;
    const btn = document.getElementById('copyBtn');
    const originalText = btn.textContent;
    
    try {
        // Usar la API moderna del portapapeles
        await navigator.clipboard.writeText(promptText);
        btn.textContent = '✅ Copiado!';
        btn.style.background = '#28a745';
        
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '#28a745';
        }, 2000);
    } catch (err) {
        // Fallback para navegadores antiguos
        const textarea = document.getElementById('chatgptPrompt');
        textarea.select();
        textarea.setSelectionRange(0, 99999);
        try {
            document.execCommand('copy');
            btn.textContent = '✅ Copiado!';
            btn.style.background = '#28a745';
            setTimeout(() => {
                btn.textContent = originalText;
                btn.style.background = '#28a745';
            }, 2000);
        } catch (fallbackErr) {
            alert('Error al copiar. Por favor, selecciona y copia manualmente.');
        }
    }
});

// Sistema de rating
let currentRating = 0;

document.querySelectorAll('.star').forEach(star => {
    star.addEventListener('click', function() {
        const rating = parseInt(this.getAttribute('data-rating'));
        setRating(rating);
    });
    
    star.addEventListener('mouseenter', function() {
        const rating = parseInt(this.getAttribute('data-rating'));
        highlightStars(rating);
    });
});

document.querySelector('.stars').addEventListener('mouseleave', function() {
    highlightStars(currentRating);
});

function setRating(rating) {
    currentRating = rating;
    highlightStars(rating);
}

function highlightStars(rating) {
    document.querySelectorAll('.star').forEach((star, index) => {
        if (index < rating) {
            star.classList.add('active');
        } else {
            star.classList.remove('active');
        }
    });
}

function resetRating() {
    currentRating = 0;
    highlightStars(0);
}

// Función para guardar selección
document.getElementById('saveBtn').addEventListener('click', function() {
    if (currentRating === 0) {
        alert('Por favor, califica la selección antes de guardar.');
        return;
    }
    
    const formData = new FormData(document.getElementById('recipeForm'));
    const selections = {};
    
    // Recopilar todas las selecciones (mismo código que en generateRecipe)
    const fields = [
        'tiempo_comida', 'tipo_cocina', 'nivel_saludable', 'cantidad_personas',
        'presupuesto', 'tiempo_disponible', 'intensidad_sabor', 'tipo_ocasion',
        'nivel_habilidad'
    ];
    
    fields.forEach(field => {
        const value = formData.get(field);
        if (value && value !== 'Cualquiera') {
            selections[field] = value;
        }
    });
    
    const checkboxFields = [
        'metodo_preparacion', 'tipo_proteina', 'base_plato', 
        'preferencias', 'tipo_plato'
    ];
    
    checkboxFields.forEach(field => {
        const values = formData.getAll(field);
        const filtered = values.filter(v => v !== 'Cualquiera');
        if (filtered.length > 0) {
            selections[field] = filtered;
        }
    });
    
    const prompt = document.getElementById('chatgptPrompt').value;
    
    const savedItem = {
        id: Date.now(),
        date: new Date().toLocaleString('es-GT'),
        rating: currentRating,
        selections: selections,
        prompt: prompt
    };
    
    // Guardar en localStorage
    let savedRecipes = JSON.parse(localStorage.getItem('savedRecipes') || '[]');
    savedRecipes.unshift(savedItem); // Agregar al inicio
    localStorage.setItem('savedRecipes', JSON.stringify(savedRecipes));
    
    // Mostrar mensaje
    const message = document.getElementById('savedMessage');
    message.classList.remove('hidden');
    setTimeout(() => {
        message.classList.add('hidden');
    }, 3000);
    
    // Actualizar historial
    loadHistory();
});

// Función para escapar HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Función para cargar historial
function loadHistory() {
    const savedRecipes = JSON.parse(localStorage.getItem('savedRecipes') || '[]');
    const historyList = document.getElementById('historyList');
    
    if (savedRecipes.length === 0) {
        historyList.innerHTML = '<p style="text-align: center; color: #666;">No hay selecciones guardadas aún.</p>';
        return;
    }
    
    let html = '';
    savedRecipes.forEach(item => {
        const stars = '⭐'.repeat(item.rating);
        const summary = Object.entries(item.selections)
            .map(([key, value]) => {
                const displayValue = Array.isArray(value) ? value.join(', ') : value;
                return `${escapeHtml(key)}: ${escapeHtml(displayValue)}`;
            })
            .join(' | ');
        
        html += `
            <div class="history-item">
                <div class="history-item-header">
                    <span class="history-item-date">📅 ${escapeHtml(item.date)}</span>
                    <span class="history-item-rating">${stars}</span>
                </div>
                <div class="history-item-summary">${summary}</div>
                <details class="history-item-prompt-container">
                    <summary style="cursor: pointer; color: #667eea; font-weight: bold; margin-bottom: 10px;">
                        📋 Ver prompt completo
                    </summary>
                    <div class="history-item-prompt">${escapeHtml(item.prompt)}</div>
                    <button class="btn-copy-small" onclick="copyPromptFromHistory('${item.id}')">
                        📋 Copiar este prompt
                    </button>
                </details>
            </div>
        `;
    });
    
    historyList.innerHTML = html;
}

// Manejar checkboxes "Cualquiera" - deseleccionar otros cuando se selecciona
document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        if (this.value === 'Cualquiera' && this.checked) {
            // Si se selecciona "Cualquiera", deseleccionar todos los demás del mismo grupo
            const name = this.name;
            document.querySelectorAll(`input[name="${name}"]`).forEach(cb => {
                if (cb !== this) {
                    cb.checked = false;
                }
            });
        } else if (this.checked && this.value !== 'Cualquiera') {
            // Si se selecciona otro, deseleccionar "Cualquiera"
            const name = this.name;
            const cualquiera = document.querySelector(`input[name="${name}"][value="Cualquiera"]`);
            if (cualquiera) {
                cualquiera.checked = false;
            }
        }
    });
});

// Función para copiar prompt desde el historial
window.copyPromptFromHistory = async function(id) {
    const savedRecipes = JSON.parse(localStorage.getItem('savedRecipes') || '[]');
    const item = savedRecipes.find(r => r.id.toString() === id);
    
    if (!item) return;
    
    try {
        await navigator.clipboard.writeText(item.prompt);
        alert('✅ Prompt copiado al portapapeles');
    } catch (err) {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = item.prompt;
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            alert('✅ Prompt copiado al portapapeles');
        } catch (fallbackErr) {
            alert('Error al copiar. Por favor, copia manualmente.');
        }
        document.body.removeChild(textarea);
    }
};

// Cargar historial al iniciar
loadHistory();

