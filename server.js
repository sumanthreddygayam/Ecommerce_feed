// Import required packages
require('dotenv').config();
const express = require('express');
const { MongoClient } = require('mongodb');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

// Initialize Express app
const app = express();
const port = 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// MongoDB Connection
const uri = process.env.MONGO_URI;
const client = new MongoClient(uri);
let db;

async function connectDB() {
    try {
        await client.connect();
        db = client.db('ecommerce');
        console.log("Successfully connected to MongoDB Atlas!");
    } catch (e) {
        console.error("Could not connect to MongoDB Atlas", e);
        process.exit(1);
    }
}

// --- API Endpoints ---

// 1. GET Endpoint to provide items from Online-eCommerce.csv
app.get('/api/items', (req, res) => {
    // Point to the new CSV file
    const csvFilePath = path.join(__dirname, 'data', 'Online-eCommerce.csv');

    fs.readFile(csvFilePath, 'utf8', (err, data) => {
        if (err) {
            console.error("Error reading the CSV file:", err);
            return res.status(500).json({ message: "Could not read data file." });
        }

        try {
            const lines = data.trim().split('\n');
            const header = lines.shift().split(',');

            // Find the indices of the new columns we need
            const orderIndex = header.indexOf('Order_Number');
            const productIndex = header.indexOf('Product');
            const categoryIndex = header.indexOf('Category');
            const brandIndex = header.indexOf('Brand');

            if ([orderIndex, productIndex, categoryIndex, brandIndex].includes(-1)) {
                throw new Error('Required columns (Order_Number, Product, Category, Brand) not found.');
            }

            const itemsByCategory = {};

            lines.forEach(line => {
                const columns = line.split(',');
                const category = columns[categoryIndex]?.trim();
                
                // Create the new item object with the desired fields
                const item = {
                    order_number: columns[orderIndex]?.trim(),
                    product: columns[productIndex]?.trim(),
                    brand: columns[brandIndex]?.trim()
                };

                if (category) {
                    if (!itemsByCategory[category]) {
                        itemsByCategory[category] = [];
                    }
                    itemsByCategory[category].push(item);
                }
            });

            res.json(itemsByCategory);
        } catch (parseError) {
            console.error("Error parsing the CSV file:", parseError);
            return res.status(500).json({ message: "Could not parse data file." });
        }
    });
});

// 2. POST Endpoint to log customer events
app.post('/api/log', async (req, res) => {
    try {
        const eventCollection = db.collection('events');
        const eventData = req.body; // This will now contain order_number, product, etc.
        eventData.serverTimestamp = new Date();
        await eventCollection.insertOne(eventData);
        res.status(201).json({ message: 'Event logged successfully' });
    } catch (error) {
        console.error('Failed to log event:', error);
        res.status(500).json({ message: 'Error logging event' });
    }
});

// Start the server after connecting to the DB
connectDB().then(() => {
    app.listen(port, () => {
        console.log(`Server running at http://localhost:${port}`);
    });
});