#!/usr/bin/env python3
"""
Podcast Author Classification Script
Classifies podcast authors as corporate/organizational vs individual.

This script analyzes author names from podcast CSV files and applies
intelligent pattern matching to identify corporate entities. Results are
saved back to CSV and a summary is posted to GitHub.

Author: mowPod BDR Bot
Date: 2026-06-24
"""

import pandas as pd
import re
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
from typing import Tuple, Dict, List

# =============================================================================
# CLASSIFICATION RULES & DATA
# =============================================================================

# Corporate keywords that indicate organizational entities
CORPORATE_KEYWORDS = {
    # Legal entity types
    'inc', 'incorporated', 'llc', 'ltd', 'corp', 'corporation', 'co',
    'company', 'group', 'enterprises', 'holdings', 'partners', 'partnership',
    'pty', 'gmbh', 'ag', 's.a.', 'sarl',
    
    # Educational institutions
    'university', 'college', 'institute', 'school', 'academy', 'education',
    'learning', 'edu',
    
    # Organizations & associations
    'organization', 'association', 'society', 'foundation', 'trust',
    'nonprofit', 'non-profit', 'charity', 'council', 'board',
    
    # Media & broadcasting
    'media', 'network', 'broadcast', 'studio', 'productions', 'radio',
    'entertainment', 'digital',
    
    # Business & professional services
    'agency', 'consulting', 'consultancy', 'firm', 'capital', 'ventures',
    'investment', 'services', 'solutions', 'tech', 'technologies',
    
    # Religious & community
    'church', 'ministry', 'ministries', 'synagogue', 'mosque', 'temple',
    'diocese', 'parish', 'community', 'center',
    
    # Government & public
    'government', 'state', 'federal', 'city', 'municipal', 'department',
    'public', 'police', 'military',
    
    # Other organizational indicators
    'publishing', 'records', 'records', 'labs', 'lab', 'research',
    'pharmaceutical', 'hospital', 'clinic', 'medical'
}

# Known corporate/branded entities (manually curated)
# NOTE: Use longer phrases where possible to avoid false positives
# e.g., "John Smith" should not match "smith"
KNOWN_CORPORATES = {
    'medscape', 'spotify', 'apple podcasts', 'google podcasts', 'amazon music',
    'netflix', 'microsoft', 'meta', 'facebook', 'instagram', 'tiktok', 'youtube',
    'iheartmedia', 'sirius xm', 'siriusxm', 'pandora', 'audible',
    'npr', 'bbc', 'cnn', 'nyt', 'new york times', 'washington post',
    'wired', 'the verge', 'techcrunch', 'vice', 'buzzfeed',
    'ted talks', 'ted', 'coursera', 'udemy', 'masterclass',
    'time magazine', 'rolling stone', 'variety', 'deadline',
    'mckinsey', 'boston consulting', 'bain', 'deloitte', 'pwc',
    'goldman sachs', 'jpmorgan', 'morgan stanley', 'bank of america',
    'tesla', 'slack', 'stripe', 'airbnb', 'uber',
    'harvard', 'stanford', 'yale', 'mit', 'oxford', 'cambridge',
    'johnson & johnson', 'procter & gamble', 'nestle', 'unilever',
    'disney', 'warner bros', 'paramount', 'universal',
    'vox media', 'wondery', 'gimlet', 'stitcher',
    'bp energy', 'bp', 'shell', 'exxon', 'chevron'
}

# =============================================================================
# CLASSIFICATION LOGIC
# =============================================================================

def is_acronym(text: str) -> bool:
    """
    Check if text is likely an acronym (2-5 consecutive uppercase letters).
    Examples: FBI, NPR, ABC, CEO (but not names like "John")
    
    Args:
        text: String to check
        
    Returns:
        True if likely an acronym
    """
    # Remove punctuation and extra spaces
    text = re.sub(r'[.,\-&]', '', text.strip())
    
    # Check for all-caps acronym pattern (2-5 consecutive uppercase letters)
    # But exclude common first names that happen to be all caps
    if re.match(r'^[A-Z]{2,5}$', text):
        # Exclude single-name patterns that are likely personal names
        common_names = {'MAX', 'JOE', 'BOB', 'ANN', 'SAM', 'RAY', 'ROY', 'ED'}
        return text not in common_names
    
    return False


def contains_corporate_keyword(author_name: str) -> bool:
    """
    Check if author name contains known corporate indicators.
    
    Args:
        author_name: Author name to check
        
    Returns:
        True if corporate keyword found
    """
    if pd.isna(author_name):
        return False
    
    author_lower = str(author_name).lower()
    
    # Check for direct keyword matches
    for keyword in CORPORATE_KEYWORDS:
        # Use word boundaries to avoid partial matches
        if re.search(rf'\b{re.escape(keyword)}\b', author_lower):
            return True
    
    return False


def contains_known_brand(author_name: str) -> bool:
    """
    Check if author name is a known corporate/branded entity.
    
    Args:
        author_name: Author name to check
        
    Returns:
        True if known brand found
    """
    if pd.isna(author_name):
        return False
    
    author_lower = str(author_name).lower()
    
    for brand in KNOWN_CORPORATES:
        if brand in author_lower:
            return True
    
    return False


def has_organizational_pattern(author_name: str) -> bool:
    """
    Check for common organizational naming patterns.
    
    Patterns include:
    - "[Name] & [Name]" (partnership style)
    - "[Name] + [Name]" (collaboration style)
    - "The [Organization]" (common org prefix)
    - Multiple commas or slashes (often org structures)
    
    Args:
        author_name: Author name to check
        
    Returns:
        True if organizational pattern found
    """
    if pd.isna(author_name):
        return False
    
    author = str(author_name)
    
    # Partnership patterns
    if re.search(r'.+\s+&\s+.+', author):
        return True
    
    if re.search(r'.+\s+\+\s+.+', author):
        return True
    
    # "The Organization" pattern
    if author.lower().startswith('the '):
        return True
    
    # Multiple commas/slashes suggest organizational structure
    if author.count(',') >= 2 or author.count('/') >= 2:
        return True
    
    return False


def has_plural_indicator(author_name: str) -> bool:
    """
    Check for plural words indicating organizations.
    Examples: "Mary and Friends", "The Beatles", "The Hosts"
    
    Args:
        author_name: Author name to check
        
    Returns:
        True if plural indicator found
    """
    if pd.isna(author_name):
        return False
    
    author_lower = str(author_name).lower()
    
    plural_keywords = {
        'and', 'plus', 'featuring', 'presents', 'hosts', 'team',
        'collective', 'crew', 'gang', 'partners', 'friends',
        'with', '&', 'feat'
    }
    
    for keyword in plural_keywords:
        if keyword in author_lower:
            return True
    
    return False


def classify_author(author_name: str) -> str:
    """
    Classify a single author as corporate or individual using multi-factor analysis.
    
    Classification logic (in priority order):
    1. Known corporate brands -> CORPORATE
    2. Corporate keywords -> CORPORATE
    3. Acronym pattern -> CORPORATE (assumption: organizations often use acronyms)
    4. Organizational name patterns -> CORPORATE
    5. Plural indicators -> CORPORATE
    6. Everything else -> INDIVIDUAL
    
    Edge cases:
    - Empty/null values -> UNKNOWN
    - Very short names (1-2 chars) -> INDIVIDUAL (likely initials)
    
    Args:
        author_name: Author name to classify
        
    Returns:
        "CORPORATE", "INDIVIDUAL", or "UNKNOWN"
    """
    # Handle empty/null
    if pd.isna(author_name) or not str(author_name).strip():
        return "UNKNOWN"
    
    author = str(author_name).strip()
    
    # Single letter or very short -> likely individual
    if len(author) <= 2:
        return "INDIVIDUAL"
    
    # Check all corporate indicators
    if contains_known_brand(author):
        return "CORPORATE"
    
    if contains_corporate_keyword(author):
        return "CORPORATE"
    
    if is_acronym(author):
        return "CORPORATE"
    
    if has_organizational_pattern(author):
        return "CORPORATE"
    
    if has_plural_indicator(author):
        return "CORPORATE"
    
    # Default to individual
    return "INDIVIDUAL"


# =============================================================================
# CSV PROCESSING
# =============================================================================

def process_csv(csv_path: str) -> Tuple[pd.DataFrame, Dict]:
    """
    Load CSV, classify authors, and generate statistics.
    
    Args:
        csv_path: Path to podcast_leads CSV file
        
    Returns:
        Tuple of (processed_dataframe, statistics_dict)
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        KeyError: If 'author' column doesn't exist
    """
    print(f"[{datetime.now()}] Loading CSV: {csv_path}")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    if 'author' not in df.columns:
        raise KeyError("'author' column not found in CSV")
    
    print(f"  Loaded {len(df)} rows")
    
    # Classify each author
    print(f"[{datetime.now()}] Classifying {len(df)} authors...")
    df['is_corporate'] = df['author'].apply(classify_author)
    
    # Generate statistics
    stats = {
        'total_authors': len(df),
        'corporate_count': (df['is_corporate'] == 'CORPORATE').sum(),
        'individual_count': (df['is_corporate'] == 'INDIVIDUAL').sum(),
        'unknown_count': (df['is_corporate'] == 'UNKNOWN').sum(),
        'corporate_pct': round(
            (df['is_corporate'] == 'CORPORATE').sum() / len(df) * 100, 2
        ),
        'individual_pct': round(
            (df['is_corporate'] == 'INDIVIDUAL').sum() / len(df) * 100, 2
        ),
    }
    
    # Get sample corporates for reporting
    corporates = df[df['is_corporate'] == 'CORPORATE'].head(10)
    stats['corporate_samples'] = corporates['author'].tolist() if len(corporates) > 0 else []
    
    # Get sample individuals for spot-check
    individuals = df[df['is_corporate'] == 'INDIVIDUAL'].head(10)
    stats['individual_samples'] = individuals['author'].tolist() if len(individuals) > 0 else []
    
    print(f"  Classification complete:")
    print(f"    Corporate: {stats['corporate_count']} ({stats['corporate_pct']}%)")
    print(f"    Individual: {stats['individual_count']} ({stats['individual_pct']}%)")
    print(f"    Unknown: {stats['unknown_count']}")
    
    return df, stats


def save_classified_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Save classified dataframe back to CSV.
    
    Args:
        df: Processed dataframe with is_corporate column
        output_path: Path to save CSV to
    """
    print(f"[{datetime.now()}] Saving classified CSV to {output_path}")
    df.to_csv(output_path, index=False)
    print(f"  ✓ Saved {len(df)} rows")


# =============================================================================
# GITHUB INTEGRATION
# =============================================================================

def post_github_summary(stats: Dict, csv_filename: str) -> None:
    """
    Post a summary comment to GitHub issue #1 with classification results.
    
    Args:
        stats: Statistics dictionary from process_csv
        csv_filename: Name of the classified CSV file for reference
        
    Raises:
        EnvironmentError: If GITHUB_TOKEN not set
        subprocess.CalledProcessError: If GitHub CLI call fails
    """
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("⚠ GITHUB_TOKEN not set, skipping GitHub comment")
        return
    
    repo = os.getenv('GITHUB_REPOSITORY', 'chaseh2/mowpod-bdr-bot')
    
    # Build markdown comment
    comment = f"""## 📊 Daily Author Classification Report
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

### Summary Statistics
| Metric | Count | Percentage |
|--------|-------|-----------|
| **Total Authors** | {stats['total_authors']} | 100% |
| **Corporate** | {stats['corporate_count']} | {stats['corporate_pct']}% |
| **Individual** | {stats['individual_count']} | {stats['individual_pct']}% |
| **Unknown** | {stats['unknown_count']} | {round(stats['unknown_count']/stats['total_authors']*100, 2)}% |

### Corporate Entities Identified (Sample)
Top examples of identified corporate authors:
"""
    
    if stats['corporate_samples']:
        for author in stats['corporate_samples'][:5]:
            comment += f"\n- `{author}`"
    else:
        comment += "\n- None found in this batch"
    
    comment += f"\n\n### Individual Authors (Sample)\n"
    if stats['individual_samples']:
        for author in stats['individual_samples'][:5]:
            comment += f"\n- `{author}`"
    else:
        comment += "\n- None found in this batch"
    
    comment += f"\n\n### Files\n"
    comment += f"- Classified CSV: `{csv_filename}`\n"
    comment += f"- Total rows processed: {stats['total_authors']}\n"
    
    comment += "\n---\n*This report was auto-generated by mowPod BDR Bot*"
    
    try:
        print(f"[{datetime.now()}] Posting summary to GitHub issue...")
        
        # Create GitHub CLI command (requires gh CLI to be installed)
        # Alternative: use PyGithub or requests with GitHub API
        result = subprocess.run(
            [
                'gh', 'issue', 'comment', '1',
                '--repo', repo,
                '--body', comment
            ],
            env={**os.environ, 'GH_TOKEN': github_token},
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("  ✓ Comment posted successfully")
        else:
            print(f"  ⚠ Failed to post comment: {result.stderr}")
            
    except Exception as e:
        print(f"  ⚠ Error posting to GitHub: {e}")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution flow."""
    print("=" * 80)
    print("PODCAST AUTHOR CLASSIFICATION ANALYSIS")
    print("=" * 80)
    
    # Find the latest podcast_leads CSV
    csv_files = list(Path('.').glob('podcast_leads_*.csv'))
    
    if not csv_files:
        print("❌ No podcast_leads_*.csv files found in current directory")
        return 1
    
    # Use most recent file
    csv_path = str(sorted(csv_files)[-1])
    csv_filename = Path(csv_path).name
    
    print(f"Using CSV: {csv_filename}\n")
    
    try:
        # Process CSV
        df, stats = process_csv(csv_path)
        
        # Save classified version
        output_path = csv_path.replace('.csv', '_classified.csv')
        save_classified_csv(df, output_path)
        
        # Post to GitHub
        post_github_summary(stats, csv_filename)
        
        print("\n" + "=" * 80)
        print("✓ CLASSIFICATION COMPLETE")
        print("=" * 80)
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())
