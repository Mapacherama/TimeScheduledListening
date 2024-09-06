# Define your variables
$client_id = "98c8b3c52bd948e4b14fe06e2df5f61b"
$client_secret = "987bba6c6528417c82d683e8e1609522"

# Create the header hashtable
$headers = @{
    "Content-Type" = "application/x-www-form-urlencoded"
}

# Create the body hashtable
$body = @{
    grant_type    = "client_credentials"
    client_id     = $client_id
    client_secret = $client_secret
}

# Execute the request to get the access token
$response = Invoke-WebRequest -Uri "https://accounts.spotify.com/api/token" `
                              -Method Post `
                              -Headers $headers `
                              -Body $body `
                              -ContentType "application/x-www-form-urlencoded"

# Convert the JSON response to a PowerShell object
$tokenResponse = $response.Content | ConvertFrom-Json

# Output the token to console
$tokenResponse.access_token
