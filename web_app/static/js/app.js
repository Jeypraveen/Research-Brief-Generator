// Research Brief Generator - Frontend JavaScript

class ResearchBriefGenerator {
    constructor() {
        this.isGenerating = false;
        this.currentStep = 0;
        this.steps = [
            'context_summarization',
            'planning', 
            'search',
            'content_fetching',
            'synthesis',
            'post_processing'
        ];
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.updateCharCount();
    }
    
    bindEvents() {
        // Form submission
        $('#research-form').on('submit', (e) => this.handleFormSubmit(e));
        
        // Character count for textarea
        $('#topic').on('input', () => this.updateCharCount());
        
        // Enter key in textarea should not submit form
        $('#topic').on('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                $(e.target).val($(e.target).val() + '\\n');
                this.updateCharCount();
            }
        });
    }
    
    updateCharCount() {
        const textarea = $('#topic');
        const charCount = $('.char-count');
        const currentLength = textarea.val().length;
        const maxLength = 500;
        
        charCount.text(`${currentLength}/${maxLength}`);
        
        if (currentLength > maxLength * 0.9) {
            charCount.css('color', '#e53e3e');
        } else {
            charCount.css('color', '#718096');
        }
    }
    
    async handleFormSubmit(e) {
        e.preventDefault();
        
        if (this.isGenerating) {
            return;
        }
        
        const formData = this.getFormData();
        
        if (!this.validateForm(formData)) {
            return;
        }
        
        this.startGeneration(formData);
    }
    
    getFormData() {
        return {
            topic: $('#topic').val().trim(),
            depth: parseInt($('#depth').val()),
            follow_up: $('#follow_up').is(':checked')
        };
    }
    
    validateForm(data) {
        if (!data.topic) {
            this.showError('Please enter a research topic');
            return false;
        }
        
        if (data.topic.length < 10) {
            this.showError('Research topic must be at least 10 characters long');
            return false;
        }
        
        if (data.topic.length > 500) {
            this.showError('Research topic must be less than 500 characters');
            return false;
        }
        
        return true;
    }
    
    async startGeneration(formData) {
        this.isGenerating = true;
        this.hideContainers();
        this.showProgress();
        this.setButtonLoading(true);
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showResults(result.brief, result.processing_time);
            } else {
                this.showError(result.error || 'An unknown error occurred');
            }
            
        } catch (error) {
            console.error('Generation error:', error);
            this.showError('Network error: Unable to connect to server');
        } finally {
            this.isGenerating = false;
            this.setButtonLoading(false);
            this.hideProgress();
        }
    }
    
    showProgress() {
        $('#progress-container').show();
        this.simulateProgress();
    }
    
    hideProgress() {
        $('#progress-container').hide();
        this.resetProgress();
    }
    
    simulateProgress() {
        this.currentStep = 0;
        const progressFill = $('.progress-fill');
        const steps = $('.step');
        
        // Reset all steps
        steps.removeClass('active completed');
        progressFill.css('width', '0%');
        
        // Simulate progress through steps
        const stepDuration = 3000; // 3 seconds per step
        const totalSteps = this.steps.length;
        
        const progressInterval = setInterval(() => {
            if (this.currentStep < totalSteps && this.isGenerating) {
                // Mark previous step as completed
                if (this.currentStep > 0) {
                    $(`[data-step="${this.steps[this.currentStep - 1]}"]`).removeClass('active').addClass('completed');
                }
                
                // Mark current step as active
                $(`[data-step="${this.steps[this.currentStep]}"]`).addClass('active');
                
                // Update progress bar
                const progress = ((this.currentStep + 1) / totalSteps) * 100;
                progressFill.css('width', `${progress}%`);
                
                this.currentStep++;
            } else {
                // Complete all steps
                steps.removeClass('active').addClass('completed');
                progressFill.css('width', '100%');
                clearInterval(progressInterval);
            }
        }, stepDuration);
        
        // Store interval ID for cleanup
        this.progressInterval = progressInterval;
    }
    
    resetProgress() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        $('.step').removeClass('active completed');
        $('.progress-fill').css('width', '0%');
        this.currentStep = 0;
    }
    
    showResults(brief, processingTime) {
        const resultsHtml = this.generateResultsHtml(brief, processingTime);
        $('#results-container').html(resultsHtml).show();
        
        // Scroll to results
        $('#results-container')[0].scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
    
    generateResultsHtml(brief, processingTime) {
        const confidence = brief.confidence_score || 0;
        const confidencePercent = Math.round(confidence * 100);
        const confidenceColor = confidence > 0.8 ? '#38a169' : confidence > 0.6 ? '#d69e2e' : '#e53e3e';
        
        return `
            <div class="brief-header">
                <h2 class="brief-title">${this.escapeHtml(brief.topic)}</h2>
                <div class="brief-meta">
                    <span>📅 Generated: ${this.formatDate(brief.generated_at)}</span>
                    <span>⏱️ Processing Time: ${processingTime.toFixed(1)}s</span>
                    <span class="confidence-score" style="background-color: ${confidenceColor}20; color: ${confidenceColor}">
                        🎯 Confidence: ${confidencePercent}%
                    </span>
                </div>
            </div>
            
            <div class="brief-section">
                <h3 class="section-title">📋 Executive Summary</h3>
                <p>${this.escapeHtml(brief.executive_summary)}</p>
            </div>
            
            <div class="brief-section">
                <h3 class="section-title">🔍 Key Findings</h3>
                <ul class="key-findings-list">
                    ${brief.key_findings.map(finding => 
                        `<li>💡 ${this.escapeHtml(finding)}</li>`
                    ).join('')}
                </ul>
            </div>
            
            <div class="brief-section">
                <h3 class="section-title">📊 Detailed Analysis</h3>
                <p>${this.escapeHtml(brief.detailed_analysis)}</p>
            </div>
            
            <div class="brief-section">
                <h3 class="section-title">💡 Recommendations</h3>
                <ul class="recommendations-list">
                    ${brief.recommendations.map(rec => 
                        `<li>✅ ${this.escapeHtml(rec)}</li>`
                    ).join('')}
                </ul>
            </div>
            
            <div class="brief-section">
                <h3 class="section-title">📚 Sources</h3>
                <div class="sources-grid">
                    ${brief.sources.map(source => `
                        <div class="source-item">
                            <div class="source-title">${this.escapeHtml(source.title)}</div>
                            <a href="${this.escapeHtml(source.url)}" class="source-url" target="_blank" rel="noopener">
                                ${this.escapeHtml(source.url)}
                            </a>
                            <p class="source-summary">${this.escapeHtml(source.summary)}</p>
                            ${source.key_points && source.key_points.length > 0 ? `
                                <div class="source-key-points">
                                    <strong>Key Points:</strong>
                                    <ul>
                                        ${source.key_points.map(point => 
                                            `<li>${this.escapeHtml(point)}</li>`
                                        ).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
            
            ${brief.research_steps && brief.research_steps.length > 0 ? `
                <div class="brief-section">
                    <h3 class="section-title">🔬 Research Steps</h3>
                    <div class="research-steps">
                        ${brief.research_steps.map(step => `
                            <div class="research-step">
                                <strong>Step ${step.step_number}:</strong> ${this.escapeHtml(step.action)}
                                ${step.key_findings ? `<br><em>Findings: ${this.escapeHtml(step.key_findings)}</em>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${brief.limitations && brief.limitations.length > 0 ? `
                <div class="brief-section">
                    <h3 class="section-title">⚠️ Limitations</h3>
                    <ul class="limitations-list">
                        ${brief.limitations.map(limitation => 
                            `<li>${this.escapeHtml(limitation)}</li>`
                        ).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <div class="brief-actions-bottom">
                <button class="generate-btn" onclick="window.researchGenerator.startNewResearch()">
                    🔄 Generate New Brief
                </button>
                <button class="export-btn" onclick="window.researchGenerator.exportResults()">
                    📄 Export Results
                </button>
            </div>
        `;
    }
    
    showError(message) {
        $('#error-message').text(message);
        $('#error-container').show();
        
        // Scroll to error
        $('#error-container')[0].scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
    
    hideContainers() {
        $('#results-container, #error-container').hide();
    }
    
    setButtonLoading(isLoading) {
        const btn = $('#generate-btn');
        const btnText = $('.btn-text');
        const btnLoading = $('.btn-loading');
        
        btn.prop('disabled', isLoading);
        
        if (isLoading) {
            btnText.hide();
            btnLoading.show();
        } else {
            btnText.show();
            btnLoading.hide();
        }
    }
    
    startNewResearch() {
        this.hideContainers();
        $('#topic').focus();
        
        // Scroll to top
        $('html, body').animate({
            scrollTop: 0
        }, 500);
    }
    
    exportResults() {
        // Simple text export - in a real app, you might generate PDF or formatted document
        const brief = this.extractBriefData();
        if (!brief) {
            alert('No brief data to export');
            return;
        }
        
        const exportText = this.generateExportText(brief);
        
        // Create and download text file
        const blob = new Blob([exportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `research-brief-${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    extractBriefData() {
        // Extract brief data from displayed results
        const title = $('.brief-title').text();
        const summary = $('.brief-section p').first().text();
        
        if (!title) {
            return null;
        }
        
        return {
            title: title,
            summary: summary,
            // Add more extraction logic as needed
        };
    }
    
    generateExportText(brief) {
        return `Research Brief: ${brief.title}
Generated: ${new Date().toISOString()}
        
Executive Summary:
${brief.summary}

---
Generated by Research Brief Generator
Built with LangGraph, Gemini 1.5 Flash, and Flask
`;
    }
    
    formatDate(dateString) {
        if (!dateString) {
            return new Date().toLocaleString();
        }
        
        try {
            return new Date(dateString).toLocaleString();
        } catch {
            return dateString;
        }
    }
    
    escapeHtml(text) {
        if (typeof text !== 'string') {
            return '';
        }
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global retry function
window.retryGeneration = function() {
    $('#error-container').hide();
    window.researchGenerator.startGeneration(window.researchGenerator.getFormData());
};

// Initialize when DOM is ready
$(document).ready(function() {
    window.researchGenerator = new ResearchBriefGenerator();
    
    // Add some nice loading effects
    $('body').addClass('loaded');
    
    // Add focus effects
    $('input, textarea, select').on('focus', function() {
        $(this).parent().addClass('focused');
    }).on('blur', function() {
        $(this).parent().removeClass('focused');
    });
    
    // Add hover effects to buttons
    $('.generate-btn, .retry-btn, .export-btn, .share-btn').on('mouseenter', function() {
        $(this).addClass('hovered');
    }).on('mouseleave', function() {
        $(this).removeClass('hovered');
    });
});

// Add some additional CSS classes dynamically
$('<style>')
    .text(`
        .loaded {
            animation: fadeIn 0.5s ease-out;
        }
        
        .focused {
            transform: scale(1.02);
            transition: transform 0.2s ease;
        }
        
        .hovered {
            transform: translateY(-1px);
        }
        
        .research-step {
            background: #f7fafc;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }
        
        .limitations-list {
            list-style: none;
            padding: 0;
        }
        
        .limitations-list li {
            background: #fef5e7;
            margin-bottom: 8px;
            padding: 10px;
            border-radius: 6px;
            border-left: 3px solid #d69e2e;
        }
        
        .brief-actions-bottom {
            margin-top: 40px;
            text-align: center;
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .source-key-points {
            margin-top: 10px;
            font-size: 0.9em;
        }
        
        .source-key-points ul {
            margin: 5px 0 0 20px;
        }
        
        .source-summary {
            margin: 8px 0;
            color: #4a5568;
            font-size: 0.95em;
        }
    `)
    .appendTo('head');