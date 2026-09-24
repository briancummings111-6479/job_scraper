/**
 * Google Apps Script to check job links for expiry and flag/delete rows.
 */

const CONFIG = {
  sheetName: "Redding Area Job Postings", // Updated to match your sheet
  urlColumnIndex: 10, // Column J is the 10th column
  statusColumnIndex: 11, // Column K (11) to write the status
  jobTitleColumnIndex: 2, // Column B for the Job Title
  addressColumnIndex: 4, // Column D for Job Site Address
  startRow: 2, 
  deleteInvalidRows: false, 
  expiredMessages: [
    "This job has expired on Indeed",
    "The job below is no longer available"
  ],
  // Optional Premium Scraping Proxy Configuration
  scraperApiKey: "a8d28a32-e465-467b-8497-ecd134c538b9", 
  scraperApiProvider: "brightdata", // Options: "brightdata", "scraperapi", "zenrows"
  brightdataZone: "jop_scraper_script_1" // Zone name required for Bright Data
};

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Job Scraper Menu')
      .addItem('Check Expired Jobs', 'checkExpiredJobs')
      .addItem('Remove Line Breaks', 'removeLineBreaks')
      .addSeparator()
      .addItem('📍 Popup Map for Selected Address', 'showMapDialog')
      .addItem('🗺️ Open Map Sidebar (Auto-Update)', 'showMapSidebar')
      .addSeparator()
      .addItem('Setup Checkboxes Column', 'setupCheckboxes')
      .addItem('Export Selected Jobs', 'exportSelectedJobs')
      .addToUi();
}

function checkExpiredJobs() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(CONFIG.sheetName);
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Sheet '" + CONFIG.sheetName + "' not found. Please update CONFIG.sheetName.");
    return;
  }

  const lastRow = sheet.getLastRow();
  if (lastRow < CONFIG.startRow) return;

  for (let i = lastRow; i >= CONFIG.startRow; i--) {
    const jobTitle = String(sheet.getRange(i, CONFIG.jobTitleColumnIndex).getValue()).trim();
    const range = sheet.getRange(i, CONFIG.urlColumnIndex);
    let url = range.getValue();
    
    // 1. Check if it's a Rich Text link
    const richText = range.getRichTextValue();
    if (richText && richText.getLinkUrl()) {
      url = richText.getLinkUrl();
    }
    
    // 2. Check if it's a HYPERLINK formula
    const formula = range.getFormula();
    if (formula && formula.toUpperCase().includes("HYPERLINK")) {
      const match = formula.match(/HYPERLINK\(\s*"([^"]+)"/i);
      if (match) url = match[1];
    }

    url = String(url).trim();

    // If there is NO url at all, skip silently
    if (!url || url === "") {
      continue; 
    }

    // Add http:// if they just pasted www.something.com
    if (url.startsWith("www.")) {
      url = "https://" + url;
    }

    // If it still doesn't look like a URL, log that we skipped it and move on
    if (!url.startsWith("http")) {
      sheet.getRange(i, CONFIG.statusColumnIndex).setValue("Skipped - Not a valid URL: " + url.substring(0, 20));
      continue;
    }

    // Only process Indeed and Snagajob URLs. Ignore all others.
    var urlLower = url.toLowerCase();
    if (urlLower.indexOf("indeed.com") === -1 && urlLower.indexOf("snagajob.com") === -1) {
      continue;
    }

    let isInvalid = false;
    let statusMessage = "Active";
    let isBlocked = false;

    try {
      let fetchUrl = url;
      let options = {
        muteHttpExceptions: true, 
        followRedirects: true,
        headers: {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
          "Accept-Language": "en-US,en;q=0.9",
          "Cache-Control": "no-cache"
        }
      };

      let isUsingPremiumProxy = false;
      if (CONFIG.scraperApiKey && CONFIG.scraperApiKey.trim() !== "") {
        let apiKey = CONFIG.scraperApiKey.trim();
        isUsingPremiumProxy = true;
        if (CONFIG.scraperApiProvider.toLowerCase() === "scraperapi") {
          // ScraperAPI keys must be 32-character hexadecimal strings (no hyphens)
          apiKey = apiKey.replace(/-/g, "");
          fetchUrl = "http://api.scraperapi.com?api_key=" + apiKey + "&url=" + encodeURIComponent(url);
          options = {
            muteHttpExceptions: true
          };
        } else if (CONFIG.scraperApiProvider.toLowerCase() === "zenrows") {
          fetchUrl = "https://api.zenrows.com/v1/?apikey=" + apiKey + "&url=" + encodeURIComponent(url) + "&js_render=true&premium_proxy=true";
          options = {
            muteHttpExceptions: true
          };
        } else if (CONFIG.scraperApiProvider.toLowerCase() === "brightdata") {
          fetchUrl = "https://api.brightdata.com/request";
          const payload = {
            zone: CONFIG.brightdataZone || "jop_scraper_script_1",
            url: url,
            format: "raw"
          };
          options = {
            method: "post",
            contentType: "application/json",
            headers: {
              "Authorization": "Bearer " + apiKey
            },
            payload: JSON.stringify(payload),
            muteHttpExceptions: true
          };
        }
      }
      
      Utilities.sleep(1000);
      
      let response = UrlFetchApp.fetch(fetchUrl, options);
      let responseCode = response.getResponseCode();
      let html = response.getContentText();
      
      // Check for Premium Proxy authentication/billing errors and stop execution early
      if (isUsingPremiumProxy && (responseCode === 401 || responseCode === 402)) {
        SpreadsheetApp.getUi().alert("Proxy API Error (" + responseCode + "):\n\n" + html + "\n\nPlease check your API key / account settings in CONFIG.");
        return;
      }
      
      let title = "No Title";
      let titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
      if (titleMatch) {
        title = titleMatch[1].trim();
      }

      let isBotProtected = html.includes("Pardon Our Interruption") || 
                           html.includes("Cloudflare") || 
                           title.includes("Access Denied") || 
                           title.includes("Just a moment...") ||
                           responseCode === 403;

      // Fallback: If blocked, and NOT already using premium proxy, try routing through Google Translate proxy
      if (isBotProtected && !isUsingPremiumProxy) {
        try {
          const translateProxyUrl = "https://translate.google.com/translate?sl=auto&tl=en&u=" + encodeURIComponent(url);
          const fallbackResponse = UrlFetchApp.fetch(translateProxyUrl, {
            muteHttpExceptions: true,
            headers: {
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
          });
          
          if (fallbackResponse.getResponseCode() === 200) {
            const fallbackHtml = fallbackResponse.getContentText();
            let fallbackTitle = "No Title";
            let fallbackTitleMatch = fallbackHtml.match(/<title[^>]*>([^<]+)<\/title>/i);
            if (fallbackTitleMatch) {
              fallbackTitle = fallbackTitleMatch[1].trim();
            }

            const fallbackBlocked = fallbackHtml.includes("Pardon Our Interruption") || 
                                    fallbackHtml.includes("Cloudflare") || 
                                    fallbackTitle.includes("Access Denied") || 
                                    fallbackTitle.includes("Just a moment...");

            if (!fallbackBlocked) {
              html = fallbackHtml;
              responseCode = 200;
              isBotProtected = false;
              title = fallbackTitle;
            }
          }
        } catch (fallbackError) {
          // Silent catch, fall back to showing original bot block details
        }
      }
      
      if (responseCode >= 400 && responseCode !== 403) {
        isInvalid = true;
        statusMessage = "HTTP Error: " + responseCode;
      } else {
        // Strip script and style tags to avoid false matches in JSON state data or CSS templates
        const cleanHtml = html.replace(/<script[^>]*>([\s\S]*?)<\/script>/gi, "")
                              .replace(/<style[^>]*>([\s\S]*?)<\/style>/gi, "");

        for (const msg of CONFIG.expiredMessages) {
          if (isExpiredMessageReal(cleanHtml, msg)) {
            isInvalid = true;
            statusMessage = "Expired: " + msg;
            break;
          }
        }

        if (!isInvalid) {
          if (isBotProtected) {
             isBlocked = true;
             statusMessage = "Blocked by Bot Protection (" + responseCode + ")";
          } else {
             statusMessage = "Checked (" + responseCode + ") Title: " + title.substring(0, 40);
             if (!containsJobTitle(html, jobTitle)) {
               statusMessage += " - Job Title not found on page";
             }
          }
        }
      }
    } catch (e) {
      isInvalid = true;
      statusMessage = "Fetch Error: " + e.message;
    }

    if (isInvalid) {
      if (CONFIG.deleteInvalidRows) {
        sheet.getRange(i, CONFIG.statusColumnIndex).setValue("Expired/Invalid");
      } else {
        sheet.getRange(i, CONFIG.statusColumnIndex).setValue(statusMessage);
      }
    } else {
      if (!CONFIG.deleteInvalidRows || statusMessage.indexOf("Job Title not found") !== -1) {
         sheet.getRange(i, CONFIG.statusColumnIndex).setValue(statusMessage);
      }
    }
  }
  
  SpreadsheetApp.getUi().alert("Finished checking jobs.");
}

/**
 * Utility function to remove all line breaks from selected cells.
 */
function removeLineBreaks() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const range = sheet.getActiveRange();
  if (!range) {
    SpreadsheetApp.getUi().alert("Please select a range of cells first.");
    return;
  }
  
  const values = range.getValues();
  let updatedCount = 0;
  
  for (let r = 0; r < values.length; r++) {
    for (let c = 0; c < values[r].length; c++) {
      let cellValue = values[r][c];
      if (typeof cellValue === "string" && cellValue !== "") {
        // Replace carriage returns and newlines with space, then clean up double spaces
        const cleanedValue = cellValue.replace(/[\r\n]+/g, " ").replace(/\s\s+/g, " ").trim();
        if (cleanedValue !== cellValue) {
          values[r][c] = cleanedValue;
          updatedCount++;
        }
      }
    }
  }
  
  if (updatedCount > 0) {
    range.setValues(values);
    SpreadsheetApp.getUi().alert("Successfully removed line breaks from " + updatedCount + " cell(s).");
  } else {
    SpreadsheetApp.getUi().alert("No cells with line breaks were found in the selected range.");
  }
}

/**
 * Checks if the visible text on the page contains the job title.
 * Normalizes casing, special characters, and whitespace to prevent false negatives.
 */
function containsJobTitle(html, jobTitle) {
  if (!jobTitle || jobTitle === "") return true;
  
  // Normalize job title (lowercase, letters/numbers/spaces only, single spacing)
  var cleanTitle = jobTitle.toLowerCase().replace(/[^a-z0-9\s]/g, "").replace(/\s+/g, " ").trim();
  if (cleanTitle === "") return true;

  // Normalize HTML content (lowercase, strip script/style tags, strip HTML elements, letters/numbers/spaces only)
  var cleanBody = html
    .replace(/<script[^>]*>([\s\S]*?)<\/script>/gi, "")
    .replace(/<style[^>]*>([\s\S]*?)<\/style>/gi, "")
    .replace(/<[^>]*>/g, " ")
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .replace(/\s+/g, " ");

  return cleanBody.indexOf(cleanTitle) !== -1;
}

/**
 * Checks if the expired message is real (i.e., not inside a JSON string or translation map).
 * Removes quote-wrapped instances of the message and checks if it still exists.
 */
function isExpiredMessageReal(cleanHtml, msg) {
  if (cleanHtml.indexOf(msg) === -1) {
    return false;
  }
  
  // Remove occurrences wrapped in double or single quotes (standard JSON strings)
  var doubleQuoted = new RegExp('"' + msg + '"', 'gi');
  var singleQuoted = new RegExp("'" + msg + "'", 'gi');
  
  var sanitized = cleanHtml.replace(doubleQuoted, "").replace(singleQuoted, "");
  
  return sanitized.indexOf(msg) !== -1;
}

/**
 * Automatically creates checkboxes in Column N for all job post rows.
 */
function setupCheckboxes() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Redding Area Job Postings");
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Sheet 'Redding Area Job Postings' not found.");
    return;
  }
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert("No jobs found to add checkboxes to.");
    return;
  }
  
  // Set the header in Column N
  sheet.getRange("N1").setValue("Export?");
  sheet.getRange("N1").setFontWeight("bold");
  sheet.getRange("N1").setHorizontalAlignment("center");
  
  // Insert checkboxes in Column N (14) for all job rows
  const checkboxRange = sheet.getRange(2, 14, lastRow - 1, 1);
  checkboxRange.insertCheckboxes();
  
  SpreadsheetApp.getUi().alert("Checkboxes have been successfully created/verified in Column N (Export?).");
}

/**
 * Scans the checkboxes in Column N and exports checked rows to a copyable text block and Google Doc.
 */
function exportSelectedJobs() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Redding Area Job Postings");
  if (!sheet) {
    SpreadsheetApp.getUi().alert("Sheet 'Redding Area Job Postings' not found.");
    return;
  }
  
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert("No jobs found in the sheet.");
    return;
  }
  
  // Scan headers to get column indices dynamically
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const colMap = {};
  for (let i = 0; i < headers.length; i++) {
    const colName = String(headers[i]).toLowerCase().trim();
    colMap[colName] = i + 1; // 1-based index
  }
  
  // Fallbacks if headers are slightly different
  const titleCol = colMap["job_title"] || colMap["job title"] || colMap["title"] || 2;
  const companyCol = colMap["company"] || 3;
  const locationCol = colMap["location"] || 4;
  const payCol = colMap["pay"] || 5;
  const typeCol = colMap["job_type_extracted"] || colMap["type"] || colMap["job type"] || colMap["full / part time"] || colMap["full/part time"] || 6;
  const urlCol = colMap["job_url"] || colMap["job url"] || colMap["url"] || colMap["job posting"] || CONFIG.urlColumnIndex || 10;
  const checkCol = colMap["export?"] || colMap["selected"] || colMap["export"] || 14; // Column N is 14
  
  // Read all rows
  const dataRange = sheet.getRange(2, 1, lastRow - 1, Math.max(14, sheet.getLastColumn()));
  const data = dataRange.getValues();
  
  const selectedJobs = [];
  const checkedRowsIndices = [];
  
  for (let i = 0; i < data.length; i++) {
    const row = data[i];
    const isChecked = row[checkCol - 1] === true;
    if (isChecked) {
      const rawTitle = String(row[titleCol - 1] || "").trim();
      const company = String(row[companyCol - 1] || "").trim();
      const location = String(row[locationCol - 1] || "").trim();
      const pay = String(row[payCol - 1] || "").trim();
      const type = String(row[typeCol - 1] || "").trim();
      
      // Get URL (handling rich text links and hyperlink formulas)
      const sheetRowIndex = i + 2;
      let url = String(row[urlCol - 1] || "").trim();
      const cellRange = sheet.getRange(sheetRowIndex, urlCol);
      const richText = cellRange.getRichTextValue();
      if (richText && richText.getLinkUrl()) {
        url = richText.getLinkUrl();
      } else {
        const formula = cellRange.getFormula();
        if (formula && formula.toUpperCase().includes("HYPERLINK")) {
          const match = formula.match(/HYPERLINK\(\s*"([^"]+)"/i);
          if (match) url = match[1];
        }
      }
      
      const cleanTitle = cleanJobTitle(rawTitle);
      
      // Build comma-separated format
      const parts = [];
      if (cleanTitle) parts.push(cleanTitle);
      if (company) parts.push(company);
      if (location) parts.push(location);
      if (pay && pay !== "N/A" && pay !== "nan" && pay !== "") parts.push(pay);
      if (type && type !== "N/A" && type !== "nan" && type !== "") parts.push(type);
      if (url) parts.push(url);
      
      selectedJobs.push(parts.join(", "));
      checkedRowsIndices.push(sheetRowIndex);
    }
  }
  
  if (selectedJobs.length === 0) {
    SpreadsheetApp.getUi().alert("No jobs selected! Please check the boxes in Column N (Export?) first.");
    return;
  }
  
  // Format the full text (with empty lines between jobs for easier reading/selecting)
  const exportText = selectedJobs.join("\n\n");
  
  // 1. Create a Google Document in Drive
  let docUrl = "";
  try {
    const dateString = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm");
    const doc = DocumentApp.create("Selected Job Postings - " + dateString);
    const body = doc.getBody();
    body.appendParagraph("Selected Job Postings - " + dateString).setHeading(DocumentApp.ParagraphHeading.HEADING1);
    body.appendParagraph("");
    
    for (let j = 0; j < selectedJobs.length; j++) {
      body.appendParagraph((j + 1) + ". " + selectedJobs[j]);
      body.appendParagraph("");
    }
    
    doc.saveAndClose();
    docUrl = doc.getUrl();
  } catch (e) {
    Logger.log("Error creating document: " + e.message);
  }
  
  // 2. Open popup modal with text and Google Doc link
  showCopyDialog(exportText, docUrl, checkedRowsIndices);
}

/**
 * Clean up job title by removing Indeed suffix and extra whitespace.
 */
function cleanJobTitle(title) {
  if (!title) return "";
  let cleaned = title.replace(/\s*-\s*job\s*post\s*/gi, "").replace(/[\r\n]+/g, " ").replace(/\s\s+/g, " ");
  return cleaned.trim();
}

/**
 * Displays the copy-paste modal dialog to the user.
 */
function showCopyDialog(text, docUrl, checkedRowsIndices) {
  const htmlTemplate = HtmlService.createTemplate(
    '<!DOCTYPE html>' +
    '<html>' +
    '<head>' +
    '  <base target="_top">' +
    '  <style>' +
    '    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 15px; color: #3c4043; background-color: #fff; }' +
    '    h3 { color: #1a73e8; margin-top: 0; font-size: 16px; font-weight: 500; }' +
    '    textarea { width: 100%; height: 180px; font-family: monospace; font-size: 12px; padding: 10px; border: 1px solid #dadce0; border-radius: 4px; box-sizing: border-box; resize: none; background-color: #f8f9fa; }' +
    '    textarea:focus { outline: none; border-color: #1a73e8; background-color: #fff; }' +
    '    .button-container { margin-top: 15px; display: flex; gap: 8px; justify-content: flex-end; }' +
    '    button { padding: 8px 16px; border-radius: 4px; border: none; font-weight: 500; cursor: pointer; font-size: 13px; }' +
    '    .btn-primary { background-color: #1a73e8; color: white; }' +
    '    .btn-primary:hover { background-color: #1557b0; }' +
    '    .btn-secondary { background-color: #fff; color: #3c4043; border: 1px solid #dadce0; }' +
    '    .btn-secondary:hover { background-color: #f8f9fa; }' +
    '    .btn-danger { background-color: #fce8e6; color: #c5221f; border: 1px solid #fad2cf; }' +
    '    .btn-danger:hover { background-color: #fbe0dd; }' +
    '    .doc-link { margin-top: 12px; font-size: 13px; color: #5f6368; }' +
    '    .doc-link a { color: #1a73e8; text-decoration: none; font-weight: 500; }' +
    '    .doc-link a:hover { text-decoration: underline; }' +
    '    .toast { background-color: #323232; color: #fff; padding: 8px 16px; border-radius: 4px; font-size: 12px; position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.3s; pointer-events: none; }' +
    '    .toast.show { opacity: 1; }' +
    '  </style>' +
    '</head>' +
    '<body>' +
    '  <h3>Ready to Copy</h3>' +
    '  <p style="font-size: 13px; color: #5f6368; margin-top: 0; margin-bottom: 10px;">Copy the formatted job list below for SMS or email:</p>' +
    '  <textarea id="copyText" onclick="this.select()"><?= text ?></textarea>' +
    '  <? if (docUrl) { ?>' +
    '    <div class="doc-link">' +
    '      Google Doc created: <a href="<?= docUrl ?>" target="_blank">Open Document</a>' +
    '    </div>' +
    '  <? } ?>' +
    '  <div class="button-container">' +
    '    <button class="btn-primary" onclick="copyText()">Copy Text</button>' +
    '    <button class="btn-danger" id="btnClear" onclick="clearChecksAndClose()">Clear Checks & Close</button>' +
    '    <button class="btn-secondary" onclick="google.script.host.close()">Close</button>' +
    '  </div>' +
    '  <div id="toast" class="toast">Text copied to clipboard!</div>' +
    '  <script>' +
    '    function copyText() {' +
    '      const textarea = document.getElementById("copyText");' +
    '      textarea.select();' +
    '      document.execCommand("copy");' +
    '      const toast = document.getElementById("toast");' +
    '      toast.classList.add("show");' +
    '      setTimeout(() => { toast.classList.remove("show"); }, 2000);' +
    '    }' +
    '    function clearChecksAndClose() {' +
    '      document.getElementById("btnClear").disabled = true;' +
    '      document.getElementById("btnClear").innerText = "Clearing...";' +
    '      google.script.run' +
    '        .withSuccessHandler(function() { google.script.host.close(); })' +
    '        .withFailureHandler(function(err) { alert("Error: " + err.message); google.script.host.close(); })' +
    '        .clearCheckboxesInSheet(<?!= JSON.stringify(checkedRowsIndices) ?>);' +
    '    }' +
    '  <\/script>' +
    '</body>' +
    '</html>'
  );
  
  htmlTemplate.text = text;
  htmlTemplate.docUrl = docUrl;
  htmlTemplate.checkedRowsIndices = checkedRowsIndices;
  
  const htmlOutput = htmlTemplate.evaluate()
      .setWidth(500)
      .setHeight(360)
      .setSandboxMode(HtmlService.SandboxMode.IFRAME);
      
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, "Job Export Console");
}

/**
 * Callback function to uncheck selected checkboxes after export.
 */
function clearCheckboxesInSheet(checkedRowsIndices) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Redding Area Job Postings");
  if (!sheet || !checkedRowsIndices || checkedRowsIndices.length === 0) return;
  
  // Find column mapping to get the export/checkbox column
  const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  let checkCol = 14; // Default to Column N
  for (let i = 0; i < headers.length; i++) {
    const colName = String(headers[i]).toLowerCase().trim();
    if (colName === "export?" || colName === "selected" || colName === "export") {
      checkCol = i + 1;
      break;
    }
  }
  
  // Uncheck the rows
  checkedRowsIndices.forEach(rowIndex => {
    sheet.getRange(rowIndex, checkCol).setValue(false);
  });
}

/**
 * Gets map data for the currently selected row or cell.
 */
function getActiveRowMapData() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  const activeCell = sheet.getActiveCell();
  const rowIndex = activeCell.getRow();
  
  if (rowIndex < (CONFIG.startRow || 2)) {
    return { error: "Please select a job row below the header." };
  }
  
  const addressCol = CONFIG.addressColumnIndex || 4; // Column D
  const titleCol = CONFIG.jobTitleColumnIndex || 2;   // Column B
  
  const address = String(sheet.getRange(rowIndex, addressCol).getValue()).trim();
  const jobTitle = String(sheet.getRange(rowIndex, titleCol).getValue()).trim();
  
  if (!address || address === "") {
    return { error: "No address found in Column D for row " + rowIndex + "." };
  }
  
  return {
    rowIndex: rowIndex,
    jobTitle: jobTitle || ("Job #" + rowIndex),
    address: address,
    encodedAddress: encodeURIComponent(address)
  };
}

/**
 * Shows a Google Maps popup modal dialog for the selected row address in Column D.
 */
function showMapDialog() {
  const data = getActiveRowMapData();
  if (data.error) {
    SpreadsheetApp.getUi().alert(data.error);
    return;
  }
  
  const htmlContent = 
    '<!DOCTYPE html>' +
    '<html>' +
    '<head>' +
    '  <base target="_top">' +
    '  <style>' +
    '    body { font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 16px; background-color: #f8f9fa; color: #202124; }' +
    '    .card { background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); padding: 16px; margin-bottom: 12px; }' +
    '    .title { font-size: 16px; font-weight: 600; color: #1a73e8; margin: 0 0 4px 0; }' +
    '    .address { font-size: 13px; color: #5f6368; margin: 0 0 12px 0; line-height: 1.4; }' +
    '    .map-container { width: 100%; height: 320px; border-radius: 8px; overflow: hidden; border: 1px solid #dadce0; }' +
    '    iframe { width: 100%; height: 100%; border: 0; }' +
    '    .actions { display: flex; gap: 8px; margin-top: 12px; justify-content: flex-end; }' +
    '    .btn { padding: 8px 16px; font-size: 13px; font-weight: 500; border-radius: 4px; cursor: pointer; text-decoration: none; border: none; display: inline-block; }' +
    '    .btn-primary { background: #1a73e8; color: white; }' +
    '    .btn-primary:hover { background: #1557b0; }' +
    '    .btn-secondary { background: #f1f3f4; color: #3c4043; border: 1px solid #dadce0; }' +
    '    .btn-secondary:hover { background: #e8eaed; }' +
    '  </style>' +
    '</head>' +
    '<body>' +
    '  <div class="card">' +
    '    <div class="title">' + escapeHtml(data.jobTitle) + '</div>' +
    '    <div class="address">📍 ' + escapeHtml(data.address) + '</div>' +
    '    <div class="map-container">' +
    '      <iframe src="https://maps.google.com/maps?q=' + data.encodedAddress + '&t=&z=14&ie=UTF8&iwloc=&output=embed" allowfullscreen loading="lazy"></iframe>' +
    '    </div>' +
    '    <div class="actions">' +
    '      <a class="btn btn-primary" href="https://www.google.com/maps/search/?api=1&query=' + data.encodedAddress + '" target="_blank">Open in Google Maps ↗</a>' +
    '      <button class="btn btn-secondary" onclick="google.script.host.close()">Close</button>' +
    '    </div>' +
    '  </div>' +
    '</body>' +
    '</html>';
  
  const htmlOutput = HtmlService.createHtmlOutput(htmlContent)
      .setWidth(540)
      .setHeight(490)
      .setSandboxMode(HtmlService.SandboxMode.IFRAME);
      
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, "Job Site Location Map");
}

/**
 * Helper function to escape HTML characters.
 */
function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/**
 * Shows an interactive map sidebar that auto-updates when clicking rows.
 */
function showMapSidebar() {
  const htmlContent = 
    '<!DOCTYPE html>' +
    '<html>' +
    '<head>' +
    '  <base target="_top">' +
    '  <style>' +
    '    body { font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 12px; background: #f8f9fa; color: #202124; }' +
    '    .header { margin-bottom: 12px; }' +
    '    .header h3 { margin: 0 0 4px 0; font-size: 15px; color: #1a73e8; }' +
    '    .header p { margin: 0; font-size: 12px; color: #5f6368; }' +
    '    .card { background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); padding: 12px; margin-bottom: 12px; }' +
    '    .job-title { font-weight: 600; font-size: 14px; margin-bottom: 4px; color: #202124; }' +
    '    .job-address { font-size: 12px; color: #5f6368; margin-bottom: 8px; line-height: 1.4; }' +
    '    .map-box { width: 100%; height: 350px; border-radius: 6px; border: 1px solid #dadce0; overflow: hidden; background: #eee; }' +
    '    iframe { width: 100%; height: 100%; border: 0; }' +
    '    .btn-link { display: inline-block; margin-top: 8px; font-size: 12px; color: #1a73e8; text-decoration: none; font-weight: 500; }' +
    '    .btn-refresh { padding: 6px 12px; font-size: 12px; background: #1a73e8; color: white; border: none; border-radius: 4px; cursor: pointer; }' +
    '    .btn-refresh:hover { background: #1557b0; }' +
    '  </style>' +
    '</head>' +
    '<body>' +
    '  <div class="header">' +
    '    <h3>📍 Job Site Map Viewer</h3>' +
    '    <p>Click any row in the spreadsheet to load its map location.</p>' +
    '  </div>' +
    '  <button class="btn-refresh" onclick="loadSelectedMap()">Refresh Selection</button>' +
    '  <div id="content" style="margin-top: 12px;">' +
    '    <p style="font-size:12px; color:#777;">Loading current selection...</p>' +
    '  </div>' +
    '  <script>' +
    '    function loadSelectedMap() {' +
    '      google.script.run' +
    '        .withSuccessHandler(renderMap)' +
    '        .withFailureHandler(showError)' +
    '        .getActiveRowMapData();' +
    '    }' +
    '    function renderMap(data) {' +
    '      const content = document.getElementById("content");' +
    '      if (data.error) {' +
    '        content.innerHTML = \'<div class="card"><p style="color:#d93025; font-size:12px; margin:0;">\' + data.error + \'</p></div>\';' +
    '        return;' +
    '      }' +
    '      content.innerHTML = \'' +
    '        <div class="card">' +
    '          <div class="job-title">\' + escapeHtml(data.jobTitle) + \'</div>' +
    '          <div class="job-address">📍 \' + escapeHtml(data.address) + \'</div>' +
    '          <div class="map-box">' +
    '            <iframe src="https://maps.google.com/maps?q=\' + data.encodedAddress + \'&t=&z=14&ie=UTF8&iwloc=&output=embed"></iframe>' +
    '          </div>' +
    '          <a class="btn-link" href="https://www.google.com/maps/search/?api=1&query=\' + data.encodedAddress + \'" target="_blank">Open in Google Maps App ↗</a>' +
    '        </div>\';' +
    '    }' +
    '    function showError(err) {' +
    '      document.getElementById("content").innerHTML = \'<p style="color:red; font-size:12px;">\' + err.message + \'</p>\';' +
    '    }' +
    '    function escapeHtml(str) {' +
    '      return String(str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/\'/g, "&#39;");' +
    '    }' +
    '    loadSelectedMap();' +
    '    setInterval(loadSelectedMap, 2500);' +
    '  <\/script>' +
    '</body>' +
    '</html>';

  const htmlOutput = HtmlService.createHtmlOutput(htmlContent)
      .setTitle("Google Map Viewer");
  SpreadsheetApp.getUi().showSidebar(htmlOutput);
}
