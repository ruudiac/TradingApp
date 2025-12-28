document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const browseBtn = document.getElementById('browseBtn');
    const previewContainer = document.getElementById('previewContainer');
    const previewImage = document.getElementById('previewImage');
    const changeBtn = document.getElementById('changeBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');

    let selectedFile = null;

    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
    });

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file');
            return;
        }

        selectedFile = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            uploadArea.style.display = 'none';
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }

    changeBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        previewContainer.style.display = 'none';
        uploadArea.style.display = 'block';
        resultsSection.style.display = 'none';
    });

    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) {
            alert('Please select a file first');
            return;
        }

        previewContainer.style.display = 'none';
        loadingSection.style.display = 'block';
        resultsSection.style.display = 'none';

        const formData = new FormData();
        formData.append('chart', selectedFile);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            displayResults(data.analysis);
        } catch (error) {
            alert('Error analyzing chart: ' + error.message);
            previewContainer.style.display = 'block';
        } finally {
            loadingSection.style.display = 'none';
        }
    });

    newAnalysisBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        previewContainer.style.display = 'none';
        uploadArea.style.display = 'block';
        resultsSection.style.display = 'none';
    });

    function displayResults(analysis) {
        const recommendation = document.getElementById('recommendation');
        const recommendationCard = document.getElementById('recommendationCard');
        
        recommendation.textContent = analysis.overall_recommendation || 'HOLD';
        recommendation.className = 'recommendation-value';
        
        const rec = (analysis.overall_recommendation || '').toLowerCase();
        if (rec.includes('buy')) {
            recommendation.classList.add('buy');
        } else if (rec.includes('sell')) {
            recommendation.classList.add('sell');
        } else {
            recommendation.classList.add('hold');
        }

        const confidence = document.getElementById('confidence');
        confidence.textContent = analysis.confidence_level || 'N/A';

        const trend = document.getElementById('trend');
        trend.textContent = analysis.trend_direction || 'N/A';
        trend.className = 'meta-value';
        if ((analysis.trend_direction || '').toLowerCase().includes('bullish')) {
            trend.classList.add('bullish');
        } else if ((analysis.trend_direction || '').toLowerCase().includes('bearish')) {
            trend.classList.add('bearish');
        }

        const rsiBadge = document.getElementById('rsiBadge');
        const rsiDesc = document.getElementById('rsiDescription');
        if (analysis.rsi_analysis) {
            rsiBadge.textContent = analysis.rsi_analysis.signal || 'NEUTRAL';
            rsiBadge.className = 'indicator-badge ' + (analysis.rsi_analysis.signal || 'neutral').toLowerCase();
            rsiDesc.textContent = analysis.rsi_analysis.description || 'RSI analysis not available';
        }

        const macdBadge = document.getElementById('macdBadge');
        const macdDesc = document.getElementById('macdDescription');
        if (analysis.macd_analysis) {
            macdBadge.textContent = analysis.macd_analysis.signal || 'NEUTRAL';
            macdBadge.className = 'indicator-badge ' + (analysis.macd_analysis.signal || 'neutral').toLowerCase();
            macdDesc.textContent = analysis.macd_analysis.description || 'MACD analysis not available';
        }

        populateList('supportLevels', analysis.support_levels);
        populateList('resistanceLevels', analysis.resistance_levels);
        populateList('entryPoints', analysis.entry_points);
        populateList('exitPoints', analysis.exit_points);
        populateList('observations', analysis.key_observations);
        populateList('riskFactors', analysis.risk_factors);

        const fibLevels = document.getElementById('fibLevels');
        fibLevels.innerHTML = '';
        if (analysis.fibonacci_levels && analysis.fibonacci_levels.length > 0) {
            analysis.fibonacci_levels.forEach(fib => {
                const fibEl = document.createElement('div');
                fibEl.className = 'fib-level';
                fibEl.innerHTML = `
                    <span class="level">${fib.level}</span>
                    <span class="significance">${fib.significance}</span>
                `;
                fibLevels.appendChild(fibEl);
            });
        }

        document.getElementById('summary').textContent = analysis.summary || 'Analysis complete.';

        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function populateList(elementId, items) {
        const list = document.getElementById(elementId);
        list.innerHTML = '';
        
        if (items && items.length > 0) {
            items.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                list.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Not available';
            list.appendChild(li);
        }
    }
});
