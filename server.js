const express = require('express');
const { exec } = require('child_process');
const app = express();
const port = 3000;
const path = require('path'); // Import path module

// Serve static files from the current directory
app.use(express.static(__dirname));
app.use(express.json());

// Serve index.html at the root
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Route to handle scraping requests
app.get('/scrape', async (req, res) => {
    const jobTitle = req.query.jobTitle;
    const location = req.query.location;
    const numJobs = req.query.numJobs; // Note: numJobs isn't directly used in the simplified python script URL yet

    if (!jobTitle || !location || !numJobs) {
        console.error('Server: Missing parameters:', { jobTitle, location, numJobs });
        return res.status(400).json({ error: 'Missing job title, location, or number of jobs parameter' }); // Send JSON error
    }
    console.log(`Server: Received request - title: ${jobTitle}, location: ${location}, number: ${numJobs}`);

    try {
        // IMPORTANT: Use the correct python interpreter if needed (e.g., from Anaconda)
        // const pythonExecutable = '/Users/umairsaeed/anaconda3/bin/python3'; // Example
        const pythonExecutable = 'python'; // Or just 'python' or 'python3' if it's in the PATH
        const scriptPath = path.join(__dirname, 'scrape_omayzi.py');

        // Construct the command to execute the python script's main function
        // Pass arguments safely (consider using libraries for more complex cases)
        // We are calling the script directly, which will execute the __main__ block
        const pythonCommand = `${pythonExecutable} "${scriptPath}" "${jobTitle}" "${location}" "${numJobs}"`;

        console.log(`Server: Executing Python command: ${pythonCommand}`);

        const { stdout, stderr } = await new Promise((resolve, reject) => {
            // Increased maxBuffer just in case, though JSON should be smaller than full HTML
            exec(pythonCommand, { maxBuffer: 1024 * 5000 }, (error, stdout, stderr) => {
                // Log stderr from Python script for debugging
                if (stderr) {
                    console.error(`Server: Python stderr:\n${stderr}`);
                }
                // Check for Python script execution errors
                if (error) {
                    console.error(`Server: Error executing Python command: ${error.message}`);
                    // Send a JSON error response
                    return reject({ status: 500, message: `Error executing Python script: ${error.message}`, stderr: stderr });
                }
                // Check if stdout contains an error JSON from the script itself
                try {
                    const result = JSON.parse(stdout);
                    if (result && result.error) {
                         console.error(`Server: Python script returned an error: ${result.error}`);
                         // Propagate the error from the script
                         return reject({ status: 500, message: `Scraping/Parsing Error: ${result.error}` });
                    }
                } catch (parseError) {
                    // Ignore if stdout is not valid JSON (it might be valid results)
                }
                 // If no errors, resolve with stdout
                resolve({ stdout, stderr });
            });
        });

        console.log(`Server: Python script stdout length: ${stdout.length}`);
        // Attempt to parse the stdout as JSON
        try {
            const jsonData = JSON.parse(stdout);
            console.log(`Server: Successfully parsed JSON response from Python.`);
            res.setHeader('Content-Type', 'application/json');
            res.status(200).json(jsonData); // Send the parsed JSON data
        } catch (parseError) {
             console.error(`Server: Failed to parse JSON from Python stdout: ${parseError}`);
             console.error(`Server: Python stdout was:\n${stdout}`);
             res.status(500).json({ error: 'Failed to parse response from scraping script.' });
        }

    } catch (error) {
        console.error(`Server: Error in /scrape route: ${error.message || error}`);
        // Send JSON error response, including status if available
        res.status(error.status || 500).json({
            error: `An error occurred: ${error.message || 'Unknown error'}`,
            details: error.stderr || 'No stderr details'
        });
    }
});

app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
    console.log(`Serving static files from: ${__dirname}`);
});
