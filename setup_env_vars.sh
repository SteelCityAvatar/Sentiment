#!/bin/bash

# Check if running in WSL (checking both WSL1 and WSL2)
if [[ -n "${WSL_DISTRO_NAME}" ]] || [[ -n "${IS_WSL}" ]] || grep -qi microsoft /proc/version; then
    echo "WSL environment detected. Setting up Reddit API environment variables..."
    
    # Create the exports command
    EXPORTS="
# Reddit API environment variables for Sentiment Analysis project
export REDDIT_CLIENT_ID=\$(cmd.exe /c \"echo %REDDIT_CLIENT_ID%\" 2>/dev/null | tr -d '\r')
export REDDIT_CLIENT_SECRET=\$(cmd.exe /c \"echo %REDDIT_CLIENT_SECRET%\" 2>/dev/null | tr -d '\r')
export REDDIT_USER_AGENT=\$(cmd.exe /c \"echo %REDDIT_USER_AGENT%\" 2>/dev/null | tr -d '\r')
"
    
    # Check if exports already exist in .bashrc
    if ! grep -q "Reddit API environment variables for Sentiment Analysis project" ~/.bashrc; then
        echo "Adding environment variables to .bashrc..."
        echo "$EXPORTS" >> ~/.bashrc
        echo "Environment variables added successfully!"
        echo "Please run 'source ~/.bashrc' or restart your terminal to apply changes."
    else
        echo "Environment variables already exist in .bashrc"
    fi
else
    echo "This script is designed for WSL environments only."
    exit 1
fi 