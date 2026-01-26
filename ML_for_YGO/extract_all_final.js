// FINAL VERSION - Gets all replay links and outputs CSV
// Paste this in the console

(async function() {
    console.log('🔍 Extracting ALL replay links...\n');
    
    const replayLinks = new Set();
    const contentDiv = document.querySelector('#duel_records .content');
    
    if (!contentDiv) {
        console.error('❌ Could not find duel records!');
        return;
    }
    
    function extractLinks() {
        const allLinks = contentDiv.querySelectorAll('a[href*="replay"]');
        allLinks.forEach(link => {
            const href = link.href || link.getAttribute('href');
            if (href && href.includes('replay?id=')) {
                replayLinks.add(href);
            }
        });
        return replayLinks.size;
    }
    
    console.log('📜 Scrolling to load more records...');
    const scrollContainer = contentDiv.closest('.scrollpane') || contentDiv.parentElement || document.body;
    
    for (let i = 0; i < 50; i++) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
        await new Promise(r => setTimeout(r, 500));
        const count = extractLinks();
        if (i % 10 === 0) console.log(`📊 Found ${count} replay links so far...`);
    }
    
    const allLinks = Array.from(replayLinks).sort();
    console.log(`\n✅ Total: ${allLinks.length} replay links\n`);
    
    // Create CSV
    const csv = 'url\n' + allLinks.map(link => `"${link}"`).join('\n');
    
    // Try to copy, if not available, just log it
    try {
        if (typeof copy !== 'undefined') {
            copy(csv);
            console.log('✅ CSV copied to clipboard!');
        } else {
            // Create a textarea to copy from
            const textarea = document.createElement('textarea');
            textarea.value = csv;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            console.log('✅ CSV copied to clipboard!');
        }
    } catch (e) {
        console.log('⚠️ Could not copy automatically. CSV is shown below:');
    }
    
    // Always show the CSV
    console.log('\n📋 === COPY THIS CSV ===');
    console.log(csv);
    console.log('=== END CSV ===\n');
    
    console.log('💡 Copy the CSV above and save it to a .csv file');
    
    return allLinks;
})();

