/**
 * Admin Panel JavaScript
 * Handles DataTables, slide builder, charts, and admin-specific functions
 */

// Initialize DataTables with French locale
function initDataTable(tableId, options = {}) {
    const defaultOptions = {
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.6/i18n/fr-FR.json'
        },
        pageLength: 25,
        responsive: true,
        ...options
    };
    
    return $(tableId).DataTable(defaultOptions);
}

// Export table to CSV
function exportTableToCSV(tableId, filename) {
    const table = $(tableId).DataTable();
    let csv = '';
    
    // Get headers
    const headers = [];
    $(tableId + ' thead th').each(function() {
        headers.push($(this).text());
    });
    csv += headers.join(',') + '\n';
    
    // Get data
    table.rows({ search: 'applied' }).every(function() {
        const data = this.data();
        const row = [];
        for (let i = 0; i < data.length; i++) {
            // Clean HTML tags and escape commas
            let cell = typeof data[i] === 'string' ? data[i].replace(/<[^>]*>/g, '') : data[i];
            cell = cell.toString().replace(/,/g, ';');
            row.push(cell);
        }
        csv += row.join(',') + '\n';
    });
    
    // Download
    downloadCSV(csv, filename);
}

// Download CSV helper
function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Initialize Chart.js chart
function initChart(canvasId, config) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx.getContext('2d'), config);
}

// Create bar chart
function createBarChart(canvasId, labels, data, label = 'Données') {
    return initChart(canvasId, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: 'rgba(13, 110, 253, 0.7)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Create line chart
function createLineChart(canvasId, labels, data, label = 'Données') {
    return initChart(canvasId, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Create doughnut chart
function createDoughnutChart(canvasId, labels, data, colors = null) {
    if (!colors) {
        colors = [
            'rgba(13, 110, 253, 0.7)',
            'rgba(25, 135, 84, 0.7)',
            'rgba(255, 193, 7, 0.7)',
            'rgba(220, 53, 69, 0.7)',
            'rgba(13, 202, 240, 0.7)'
        ];
    }
    
    return initChart(canvasId, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true
        }
    });
}

// Slide Builder Functions
class SlideBuilder {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.slides = [];
        this.slideCounter = 0;
        
        this.initializeSortable();
    }
    
    initializeSortable() {
        if (typeof Sortable !== 'undefined' && this.container) {
            new Sortable(this.container, {
                handle: '.drag-handle',
                animation: 150,
                onEnd: () => this.updateSlideNumbers()
            });
        }
    }
    
    addSlide(type = 'text', content = '') {
        this.slideCounter++;
        
        const slideHTML = `
            <div class="slide-item card mb-3" data-index="${this.slideCounter}">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center">
                        <i class="bi bi-grip-vertical drag-handle me-2" style="cursor: move;"></i>
                        <strong class="slide-number">Diapositive ${this.slideCounter}</strong>
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button type="button" class="btn btn-outline-secondary move-up-btn" title="Monter">
                            <i class="bi bi-arrow-up"></i>
                        </button>
                        <button type="button" class="btn btn-outline-secondary move-down-btn" title="Descendre">
                            <i class="bi bi-arrow-down"></i>
                        </button>
                        <button type="button" class="btn btn-outline-danger delete-slide-btn" title="Supprimer">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-3 mb-3">
                            <label class="form-label">Type de diapositive</label>
                            <select class="form-select slide-type">
                                <option value="text" ${type === 'text' ? 'selected' : ''}>Texte</option>
                                <option value="video" ${type === 'video' ? 'selected' : ''}>Vidéo</option>
                                <option value="image" ${type === 'image' ? 'selected' : ''}>Image</option>
                                <option value="quiz" ${type === 'quiz' ? 'selected' : ''}>Quiz</option>
                            </select>
                        </div>
                        <div class="col-md-9 mb-3">
                            <label class="form-label">Contenu</label>
                            <textarea class="form-control slide-content" rows="4">${content}</textarea>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.container.insertAdjacentHTML('beforeend', slideHTML);
        
        // Attach event listeners
        const newSlide = this.container.lastElementChild;
        this.attachSlideEvents(newSlide);
        
        this.updateSlideNumbers();
    }
    
    attachSlideEvents(slideElement) {
        // Delete button
        slideElement.querySelector('.delete-slide-btn').addEventListener('click', () => {
            if (confirm('Voulez-vous vraiment supprimer cette diapositive?')) {
                slideElement.remove();
                this.updateSlideNumbers();
            }
        });
        
        // Move up button
        slideElement.querySelector('.move-up-btn').addEventListener('click', () => {
            const prev = slideElement.previousElementSibling;
            if (prev) {
                this.container.insertBefore(slideElement, prev);
                this.updateSlideNumbers();
            }
        });
        
        // Move down button
        slideElement.querySelector('.move-down-btn').addEventListener('click', () => {
            const next = slideElement.nextElementSibling;
            if (next) {
                this.container.insertBefore(next, slideElement);
                this.updateSlideNumbers();
            }
        });
    }
    
    updateSlideNumbers() {
        const slides = this.container.querySelectorAll('.slide-item');
        slides.forEach((slide, index) => {
            slide.querySelector('.slide-number').textContent = `Diapositive ${index + 1}`;
        });
    }
    
    collectSlides() {
        const slides = [];
        this.container.querySelectorAll('.slide-item').forEach((slideElement) => {
            const type = slideElement.querySelector('.slide-type').value;
            const content = slideElement.querySelector('.slide-content').value;
            
            slides.push({
                type: type,
                content: content
            });
        });
        return slides;
    }
}

// Dynamic Form Fields Management
class DynamicFormFields {
    constructor(containerId, fieldTemplate) {
        this.container = document.getElementById(containerId);
        this.template = fieldTemplate;
        this.fieldCounter = 0;
    }
    
    addField(data = {}) {
        this.fieldCounter++;
        const html = this.template(this.fieldCounter, data);
        this.container.insertAdjacentHTML('beforeend', html);
        
        // Attach delete handler
        const newField = this.container.lastElementChild;
        const deleteBtn = newField.querySelector('.delete-field-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                newField.remove();
            });
        }
    }
    
    collectFields() {
        const fields = [];
        this.container.querySelectorAll('.dynamic-field').forEach((fieldElement) => {
            const data = {};
            fieldElement.querySelectorAll('[data-field-name]').forEach((input) => {
                data[input.dataset.fieldName] = input.value;
            });
            fields.push(data);
        });
        return fields;
    }
}

// Bulk Actions Handler
class BulkActionsHandler {
    constructor(checkboxSelector, actionsConfig) {
        this.checkboxSelector = checkboxSelector;
        this.actionsConfig = actionsConfig;
        this.selectedIds = new Set();
        
        this.attachCheckboxListeners();
    }
    
    attachCheckboxListeners() {
        // Select all checkbox
        const selectAll = document.getElementById('selectAll');
        if (selectAll) {
            selectAll.addEventListener('change', (e) => {
                document.querySelectorAll(this.checkboxSelector).forEach((checkbox) => {
                    checkbox.checked = e.target.checked;
                    this.updateSelection();
                });
            });
        }
        
        // Individual checkboxes
        document.querySelectorAll(this.checkboxSelector).forEach((checkbox) => {
            checkbox.addEventListener('change', () => {
                this.updateSelection();
            });
        });
    }
    
    updateSelection() {
        this.selectedIds.clear();
        document.querySelectorAll(this.checkboxSelector + ':checked').forEach((checkbox) => {
            this.selectedIds.add(checkbox.value);
        });
        
        // Update UI
        const count = this.selectedIds.size;
        const countElement = document.getElementById('selectedCount');
        if (countElement) {
            countElement.textContent = count;
        }
        
        // Show/hide bulk actions
        const bulkActionsCard = document.getElementById('bulkActionsCard');
        if (bulkActionsCard) {
            bulkActionsCard.style.display = count > 0 ? 'block' : 'none';
        }
    }
    
    getSelectedIds() {
        return Array.from(this.selectedIds);
    }
}

// Export functions
window.AdminUtils = {
    initDataTable: initDataTable,
    exportTableToCSV: exportTableToCSV,
    initChart: initChart,
    createBarChart: createBarChart,
    createLineChart: createLineChart,
    createDoughnutChart: createDoughnutChart,
    SlideBuilder: SlideBuilder,
    DynamicFormFields: DynamicFormFields,
    BulkActionsHandler: BulkActionsHandler
};
