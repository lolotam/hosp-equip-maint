"""
Utility functions for working with environment variables and .env files.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

def update_env_value(key, value, env_path=None):
    """
    Update a specific environment variable in the .env file.

    Args:
        key: The environment variable key to update
        value: The new value to set
        env_path: Path to the .env file (optional, will use find_dotenv() if not provided)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find .env file if path not provided
        if not env_path:
            env_path = find_dotenv()
            if not env_path:
                logger.error("Could not find .env file")
                return False

        # Read current .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()

        # Update the specific key
        updated = False
        new_lines = []

        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                updated = True
            else:
                new_lines.append(line)

        # If key wasn't found, add it to the end
        if not updated:
            new_lines.append(f"{key}={value}\n")

        # Write updated .env file
        with open(env_path, 'w') as f:
            f.writelines(new_lines)

        # Reload environment variables
        load_dotenv(env_path, override=True)

        # Update os.environ as well
        os.environ[key] = value

        return True

    except Exception as e:
        logger.exception(f"Error updating environment variable {key}: {str(e)}")
        return False

def update_env_section(section_name, values, env_path=None):
    """
    Update a section of environment variables in the .env file.

    Args:
        section_name: The section name (e.g., "# Email Configuration")
        values: Dictionary of key-value pairs to update
        env_path: Path to the .env file (optional, will use find_dotenv() if not provided)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find .env file if path not provided
        if not env_path:
            env_path = find_dotenv()
            if not env_path:
                logger.error("Could not find .env file")
                return False

        # Read current .env file
        with open(env_path, 'r') as f:
            lines = f.readlines()

        # Update the section
        updated_lines = []
        in_section = False
        updated_keys = {key: False for key in values.keys()}

        for line in lines:
            # Check if we're entering the section
            if section_name in line:
                in_section = True
                updated_lines.append(line)
                continue

            # Check if we're leaving the section
            if in_section and line.startswith('#') and section_name not in line:
                # Add any keys that weren't updated before leaving the section
                for key, updated in updated_keys.items():
                    if not updated:
                        updated_lines.append(f"{key}={values[key]}\n")
                in_section = False

            # Update keys in the section
            if in_section:
                key_updated = False
                for key in values.keys():
                    if line.strip().startswith(f"{key}="):
                        # Only update the key if it's in the values dictionary
                        updated_lines.append(f"{key}={values[key]}\n")
                        updated_keys[key] = True
                        key_updated = True
                        break

                if not key_updated:
                    # Keep the original line (important for preserving passwords)
                    updated_lines.append(line)
            else:
                updated_lines.append(line)

        # If we're still in the section at the end of the file, add any remaining keys
        if in_section:
            for key, updated in updated_keys.items():
                if not updated:
                    updated_lines.append(f"{key}={values[key]}\n")

        # Write updated .env file
        with open(env_path, 'w') as f:
            f.writelines(updated_lines)

        # Reload environment variables
        load_dotenv(env_path, override=True)

        # Update os.environ as well
        for key, value in values.items():
            os.environ[key] = value

        return True

    except Exception as e:
        logger.exception(f"Error updating environment section {section_name}: {str(e)}")
        return False
