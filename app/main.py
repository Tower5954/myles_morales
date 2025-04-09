#!/usr/bin/env python3
import sys
import argparse
from contact_finder import ContactFinder
from bulk_contact_finder import BulkContactFinder
from contact_evaluator import ContactEvaluator
import os
import time

def main():
    parser = argparse.ArgumentParser(description="Find contact information for businesses")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Create and save the miles_web Ollama model")
    setup_parser.add_argument("--config", default="config.json", help="Path to config file")
    setup_parser.add_argument("--model-name", help="Override the model name (default from config)")
    
    # Find command
    find_parser = subparsers.add_parser("find", help="Find contact information")
    find_parser.add_argument("business_name", help="Business name to search for")
    find_parser.add_argument("--config", default="config.json", help="Path to config file")
    find_parser.add_argument("--url", help="Directly scrape a specific URL for more details")
    find_parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Configure the contact finder")
    config_parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Set a configuration value")
    config_parser.add_argument("--get", metavar="KEY", help="Get a configuration value")
    config_parser.add_argument("--list", action="store_true", help="List all configuration values")
    config_parser.add_argument("--config", default="config.json", help="Path to config file")
    
    # Bulk search command
    bulk_parser = subparsers.add_parser("bulk", help="Perform bulk information searches")
    bulk_parser.add_argument("--interactive", action="store_true", help="Run interactive bulk search")
    bulk_parser.add_argument("--names", nargs="+", help="List of names to search")
    bulk_parser.add_argument("--query", help="Search query to use")
    bulk_parser.add_argument("--input-file", help="File with names to search (one per line)")
    bulk_parser.add_argument("--config", default="config.json", help="Path to config file")
    
    # Find with evaluation command
    find_eval_parser = subparsers.add_parser("find-eval", help="Find and evaluate contact information")
    find_eval_parser.add_argument("business_name", help="Business name to search for")
    find_eval_parser.add_argument("--config", default="config.json", help="Path to config file")
    find_eval_parser.add_argument("--url", help="Directly scrape a specific URL for more details")
    
    # Setup eval command
    setup_eval_parser = subparsers.add_parser("setup-eval", help="Set up both miles_ai and prowler_ai models")
    setup_eval_parser.add_argument("--config", default="config.json", help="Path to config file")
    
    args = parser.parse_args()
    
    # Use config path if provided
    config_path = args.config if hasattr(args, 'config') else "config.json"
    
    if args.command == "setup":
        contact_finder = ContactFinder(config_path)
        # Override model name if provided
        if hasattr(args, 'model_name') and args.model_name:
            contact_finder.config_manager.set("model_name", args.model_name)
            print(f"Using custom model name: {args.model_name}")
        
        model_name = contact_finder.config_manager.get("model_name")
        print(f"Creating persistent Ollama model: {model_name}")
        print("This model will be available for use in any application")
        success = contact_finder.setup()
        
        if success:
            print(f"\nModel {model_name} is now available!")
            print("You can use this model in other applications with:")
            print(f"  ollama run {model_name}")
            print("Or in Python with:")
            print(f"  ollama.generate(model='{model_name}', prompt='your prompt here')")
        
        sys.exit(0 if success else 1)
    
    elif args.command == "find":
        contact_finder = ContactFinder(config_path)
        
        if args.url and not args.interactive:
            # Direct deep scrape of a specific URL
            result = contact_finder.deep_scrape_url(args.url, args.business_name)
            print("\n" + "="*80 + "\n")
            print(result)
            print("\n" + "="*80 + "\n")
        
        elif args.interactive:
            # Interactive mode
            run_interactive_mode(contact_finder, args.business_name)
        
        else:
            # Regular initial search
            result, urls = contact_finder.initial_search(args.business_name)
            print("\n" + "="*80 + "\n")
            print(result)
            print("\n" + "="*80 + "\n")
            
            if urls:
                print("Do you want to scrape any specific URL for more details? (y/n)")
                choice = input().lower()
                
                if choice == 'y':
                    # Enter interactive mode
                    run_interactive_mode(contact_finder, args.business_name, urls)
    
    elif args.command == "config":
        contact_finder = ContactFinder(config_path)
        
        if args.set:
            key, value = args.set
            # Try to convert to appropriate type
            try:
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit():
                    value = float(value)
            except:
                pass
            
            contact_finder.config_manager.set(key, value)
            print(f"Set {key} to {value}")
        
        elif args.get:
            value = contact_finder.config_manager.get(args.get)
            print(f"{args.get}: {value}")
        
        elif args.list:
            for key, value in contact_finder.config_manager.config.items():
                print(f"{key}: {value}")
    
    elif args.command == "bulk":
        bulk_finder = BulkContactFinder(config_path)
        
        if args.interactive:
            # Run interactive mode
            bulk_finder.interactive_bulk_search()
        else:
            # Validate input
            if args.input_file:
                # Read names from file
                try:
                    with open(args.input_file, 'r') as f:
                        names = [line.strip() for line in f if line.strip()]
                except FileNotFoundError:
                    print(f"Error: File {args.input_file} not found.")
                    sys.exit(1)
            elif args.names:
                names = args.names
            else:
                print("Error: Please provide names via --names or --input-file")
                sys.exit(1)
            
            # Validate query
            if not args.query:
                print("Error: Please specify search query with --query")
                sys.exit(1)
            
            # Perform bulk search
            bulk_finder.bulk_search(names, args.query)
    
    elif args.command == "find-eval":
        # Create integrated evaluator
        evaluator = ContactEvaluator(config_path)
        
        # Find and evaluate contacts
        result = evaluator.find_and_evaluate_contacts(args.business_name, 
                                                    [args.url] if args.url else None)
        
        # Display the result
        print("\n" + "="*80)
        print(result)
        print("="*80 + "\n")
        
        # Let the user know where the full results are stored
        safe_name = args.business_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        print(f"Full results saved to: contact_search_results/{safe_name}_results.json")
    
    elif args.command == "setup-eval":
        # Create integrated evaluator
        evaluator = ContactEvaluator(config_path)
        
        # Set up both models
        print("Setting up miles_ai and prowler_ai models...")
        success = evaluator.setup()
        
        if success:
            print("Both models set up successfully!")
        else:
            print("Failed to set up one or both models.")
            sys.exit(1)
    
    else:
        parser.print_help()


def run_interactive_mode(contact_finder, business_name, urls=None):
    """Run in interactive mode allowing the user to select URLs to scrape"""
    if urls is None:
        # If no URLs provided, do initial search
        result, urls = contact_finder.initial_search(business_name)
        print("\n" + "="*80 + "\n")
        print(result)
        print("\n" + "="*80 + "\n")
    
    if not urls:
        print("No URLs available to scrape.")
        return
    
    while True:
        print("\nAvailable URLs:")
        for i, url in enumerate(urls):
            print(f"[{i+1}] {url}")
        
        print("\nEnter URL number to scrape (or 'q' to quit):")
        choice = input().lower()
        
        if choice == 'q':
            break
        
        try:
            url_index = int(choice) - 1
            if 0 <= url_index < len(urls):
                result = contact_finder.deep_scrape_url(urls[url_index], business_name)
                print("\n" + "="*80 + "\n")
                print(result)
                print("\n" + "="*80 + "\n")
            else:
                print("Invalid URL number. Please try again.")
        except ValueError:
            print("Please enter a valid number or 'q' to quit.")


if __name__ == "__main__":
    main()