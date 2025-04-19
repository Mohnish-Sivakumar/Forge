#!/usr/bin/env python3
"""
Script to prepare static files for deployment to Render
This ensures all static files are available in the expected locations
"""

import os
import sys
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to prepare static files"""
    logger.info("Preparing static files for deployment")
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Project root: {project_root}")
    
    # Define source directories for static files (in order of preference)
    sources = [
        os.path.join(project_root, "my-voice-assistant", "build"),
        os.path.join(project_root, "backend", "static"),
    ]
    
    # Define target directories where static files should be available
    targets = [
        os.path.join(project_root, "api", "static"),
        os.path.join(project_root, "static")
    ]
    
    # Find a valid source directory
    source_dir = None
    for src in sources:
        if os.path.exists(src) and os.path.isdir(src):
            if os.path.exists(os.path.join(src, "index.html")):
                source_dir = src
                logger.info(f"Found valid source directory: {source_dir}")
                break
    
    if not source_dir:
        logger.error("No valid source directory found")
        return 1
    
    # Create target directories and copy files
    for target in targets:
        try:
            # Skip if it's the same as the source
            if os.path.abspath(target) == os.path.abspath(source_dir):
                logger.info(f"Skipping {target} (same as source)")
                continue
                
            # Create target directory if it doesn't exist
            os.makedirs(target, exist_ok=True)
            logger.info(f"Created directory: {target}")
            
            # Copy files from source to target
            for item in os.listdir(source_dir):
                src_item = os.path.join(source_dir, item)
                dst_item = os.path.join(target, item)
                
                if os.path.isdir(src_item):
                    # For directories like "static", copy recursively
                    if os.path.exists(dst_item):
                        shutil.rmtree(dst_item)
                    shutil.copytree(src_item, dst_item)
                    logger.info(f"Copied directory: {item} to {dst_item}")
                else:
                    # For files like index.html, just copy the file
                    shutil.copy2(src_item, dst_item)
                    logger.info(f"Copied file: {item} to {dst_item}")
            
            # Create symbolic links for CSS, JS if needed
            if "static" in os.listdir(target):
                for subdir in ["css", "js", "media"]:
                    src_subdir = os.path.join(target, "static", subdir)
                    dst_subdir = os.path.join(target, subdir)
                    
                    if os.path.exists(src_subdir) and not os.path.exists(dst_subdir):
                        try:
                            # Try to create symbolic link (won't work on Windows)
                            os.symlink(src_subdir, dst_subdir)
                            logger.info(f"Created symlink: {dst_subdir} -> {src_subdir}")
                        except:
                            # On failure (or Windows), just copy the files
                            shutil.copytree(src_subdir, dst_subdir)
                            logger.info(f"Copied directory: {src_subdir} to {dst_subdir}")
        except Exception as e:
            logger.error(f"Error copying to {target}: {e}")
    
    logger.info("Static file preparation completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 