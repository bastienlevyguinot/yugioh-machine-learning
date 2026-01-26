// PASTE THIS ENTIRE CODE INTO THE BROWSER CONSOLE
// It will scroll through all records and extract ALL replay links

(async function() {
    console.log('🔍 Extracting ALL replay links...\n');
    
    const replayLinks = new Set(); // Use Set to avoid duplicates
    const contentDiv = document.querySelector('#duel_records .content');
    
    if (!contentDiv) {
        console.error('❌ Could not find duel records! Make sure you\'re on the Duel Records page.');
        return;
    }
    
    // Function to extract all replay links currently visible
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
    
    // Initial extraction
    let count = extractLinks();
    console.log(`📊 Found ${count} replay links initially`);
    
    // Scroll through the content to trigger lazy loading
    console.log('📜 Scrolling to load more records...');
    
    const scrollContainer = contentDiv.closest('.scrollpane') || contentDiv.parentElement || document.body;
    let previousCount = 0;
    let stableCount = 0;
    
    for (let i = 0; i < 100; i++) { // Max 100 scroll attempts
        // Scroll down
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
        await new Promise(r => setTimeout(r, 300)); // Wait 300ms
        
        // Extract links
        count = extractLinks();
        
        if (count === previousCount) {
            stableCount++;
            if (stableCount >= 3) {
                // No new links found after 3 attempts, we're done
                break;
            }
        } else {
            stableCount = 0;
            console.log(`📊 Now found ${count} replay links...`);
        }
        
        previousCount = count;
    }
    
    // Final check - look for any buttons that load more
    const buttons = contentDiv.querySelectorAll('button, [onclick], .load-more, [class*="next"], [class*="more"]');
    for (const btn of buttons) {
        const text = btn.textContent.toLowerCase();
        if (text.includes('more') || text.includes('next') || text.includes('load')) {
            console.log('🔘 Found potential "load more" button, clicking...');
            btn.click();
            await new Promise(r => setTimeout(r, 1000));
            extractLinks();
        }
    }
    
    // Convert Set to Array
    const allLinks = Array.from(replayLinks).sort();
    
    console.log(`\n✅ Extraction complete!`);
    console.log(`📊 Total unique replay links: ${allLinks.length}\n`);
    
    // Create CSV format
    const csv = 'url\n' + allLinks.map(link => `"${link}"`).join('\n');
    
    // Create JSON for clipboard
    const json = JSON.stringify(allLinks.map((url, i) => ({
        number: i + 1,
        url: url,
        replay_id: url.split('id=')[1] || ''
    })), null, 2);
    
    // Copy to clipboard
    copy(csv);
    console.log('✅ CSV copied to clipboard!');
    console.log('\n📋 First 10 links:');
    allLinks.slice(0, 10).forEach((link, i) => console.log(`${i+1}. ${link}`));
    if (allLinks.length > 10) {
        console.log(`... and ${allLinks.length - 10} more`);
    }
    
    console.log('\n💡 The CSV is in your clipboard! Paste it into a text file and save as .csv');
    
    return allLinks;
})();

