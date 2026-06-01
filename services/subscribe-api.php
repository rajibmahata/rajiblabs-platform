<?php
/**
 * RajibLabs Subscriber API
 * Accepts email subscriptions and stores them.
 * Deploy to: /rajiblabs/api/subscribe/index.php on SmarterASP FTP
 */
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle CORS preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Only accept POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
    exit();
}

// Parse JSON body
$body = json_decode(file_get_contents('php://input'), true);
$email = trim($body['email'] ?? '');

if (!$email || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'Valid email required']);
    exit();
}

// Store subscriber in a JSON file
$subscribersFile = __DIR__ . '/subscribers.json';
$subscribers = [];

if (file_exists($subscribersFile)) {
    $subscribers = json_decode(file_get_contents($subscribersFile), true) ?: [];
}

// Check for duplicates
foreach ($subscribers as $sub) {
    if (($sub['email'] ?? '') === $email) {
        echo json_encode(['status' => 'ok', 'message' => 'Already subscribed!']);
        exit();
    }
}

// Add new subscriber
$subscribers[] = [
    'email' => $email,
    'subscribed_at' => date('c'),
    'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
];

file_put_contents($subscribersFile, json_encode($subscribers, JSON_PRETTY_PRINT));

// Notify both emails using mail() if configured
$subject = "🆕 New RajibLabs Subscriber";
$message = "New subscriber: {$email}\nTotal: " . count($subscribers) . "\nTime: " . date('Y-m-d H:i:s T');
$headers = "From: noreply@rajiblabs.com\r\n";

// Send to both emails
@mail('rajibmahata143@gmail.com', $subject, $message, $headers);
@mail('rajibmahata143@outlook.com', $subject, $message, $headers);

// Log for debugging
@file_put_contents(__DIR__ . '/notify.log', date('c') . " | Sent notification for: {$email}\n", FILE_APPEND);

echo json_encode([
    'status' => 'ok',
    'message' => 'Subscribed successfully!',
    'total' => count($subscribers),
]);
