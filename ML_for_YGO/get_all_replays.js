// Script to extract ALL replay links from DuelingBook
// This will scroll through all records and load all pages

async function getAllReplayLinks() {
    console.log('🔍 Starting to extract ALL replay links...\n');
    
    const replayLinks = [];
    const contentDiv = document.querySelector('#duel_records .content');
    
    if (!contentDiv) {
        console.error('❌ Could not find duel records content div!');
        return;
    }
    
    // Function to extract replay links from current DOM
    function extractCurrentLinks() {
        const links = [];
        contentDiv.querySelectorAll('a[href*="replay"]').forEach(link => {
            const href = link.href || link.getAttribute('href');
            if (href && href.includes('replay') && !links.includes(href)) {
                links.push(href);
            }
        });
        return links;
    }
    
    // Scroll to bottom to trigger lazy loading
    console.log('📜 Scrolling to load all records...');
    let lastHeight = 0;
    let scrollAttempts = 0;
    const maxScrollAttempts = 50;
    
    while (scrollAttempts < maxScrollAttempts) {
        // Scroll to bottom
        window.scrollTo(0, document.body.scrollHeight);
        
        // Wait a bit for content to load
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Check if new content loaded
        const currentHeight = document.body.scrollHeight;
        if (currentHeight === lastHeight) {
            // Check for "Load More" or "Next" buttons
            const loadMoreBtn = document.querySelector('button, [onclick*="more"], [onclick*="next"], .load-more, .next-page');
            if (loadMoreBtn && loadMoreBtn.offsetParent !== null) {
                console.log('🔘 Found load more button, clicking...');
                loadMoreBtn.click();
                await new Promise(resolve => setTimeout(resolve, 1000));
                lastHeight = 0; // Reset to continue scrolling
                scrollAttempts++;
                continue;
            } else {
                // No more content to load
                break;
            }
        }
        
        lastHeight = currentHeight;
        
        // Extract current links
        const currentLinks = extractCurrentLinks();
        replayLinks.push(...currentLinks);
        
        // Remove duplicates
        const unique = [...new Set(replayLinks)];
        replayLinks.length = 0;
        replayLinks.push(...unique);
        
        console.log(`📊 Found ${replayLinks.length} unique replay links so far...`);
        scrollAttempts++;
    }
    
    // Final extraction of all links
    console.log('🔍 Final extraction...');
    contentDiv.querySelectorAll('a[href*="replay"]').forEach(link => {
        const href = link.href || link.getAttribute('href');
        if (href && href.includes('replay') && !replayLinks.includes(href)) {
            replayLinks.push(href);
        }
    });
    
    // Remove duplicates
    const uniqueLinks = [...new Set(replayLinks)];
    
    console.log('\n✅ Extraction complete!');
    console.log(`📊 Total unique replay links found: ${uniqueLinks.length}\n`);
    
    // Display all links
    console.log('=== ALL REPLAY LINKS ===');
    uniqueLinks.forEach((link, i) => {
        console.log(`${i + 1}. ${link}`);
    });
    
    // Copy to clipboard
    const result = uniqueLinks.map((link, i) => ({
        number: i + 1,
        url: link,
        replay_id: link.split('id=')[1] || ''
    }));
    
    copy(JSON.stringify(result, null, 2));
    console.log('\n✅ Results copied to clipboard as JSON!');
    
    // Also create CSV format
    const csv = 'url,replay_id\n' + uniqueLinks.map(link => {
        const id = link.split('id=')[1] || '';
        return `"${link}","${id}"`;
    }).join('\n');
    
    console.log('\n📋 CSV format (copy this):');
    console.log(csv);
    
    return uniqueLinks;
}

// Run the function
getAllReplayLinks().then(links => {
    console.log(`\n🎉 Successfully extracted ${links.length} replay links!`);
    console.log('💡 Tip: Copy the CSV format above and save it to a .csv file');
});

