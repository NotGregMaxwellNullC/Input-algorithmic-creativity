#!/usr/bin/env python3
"""
Research Paper Analyzer
-----------------------
Simple, local tool to analyze research papers from arxiv (or local PDFs).
Extracts signal from papers: topics, keywords, methods, and a structured summary.

Usage:
    python research_analyzer.py https://arxiv.org/pdf/2504.15266
    python research_analyzer.py paper.pdf
    python research_analyzer.py https://arxiv.org/abs/2504.15266
"""

import sys
import os
import re
import math
import string
import tempfile
from collections import Counter
from pathlib import Path

import requests
from PyPDF2 import PdfReader


# ── Topic taxonomy ──────────────────────────────────────────────────────────

TOPIC_KEYWORDS = {
    "Machine Learning": [
        "neural network", "deep learning", "training", "gradient", "backpropagation",
        "loss function", "optimizer", "epoch", "batch", "overfitting", "regularization",
        "supervised", "unsupervised", "reinforcement learning", "classification",
        "regression", "feature", "embedding", "latent", "representation learning",
    ],
    "AI / LLMs": [
        "large language model", "llm", "transformer", "attention", "gpt", "bert",
        "token", "prompt", "fine-tuning", "pretraining", "next-token prediction",
        "autoregressive", "generative", "language model", "chatbot", "instruction tuning",
        "rlhf", "alignment", "in-context learning", "chain-of-thought",
    ],
    "Computer Vision": [
        "image", "convolution", "cnn", "object detection", "segmentation",
        "visual", "pixel", "resolution", "diffusion model", "gan", "vae",
        "image generation", "vision transformer", "vit",
    ],
    "NLP": [
        "natural language", "text", "corpus", "tokenization", "parsing",
        "sentiment", "named entity", "machine translation", "summarization",
        "question answering", "word embedding", "vocabulary",
    ],
    "Optimization": [
        "optimization", "convergence", "sgd", "adam", "learning rate",
        "objective function", "convex", "non-convex", "constraint",
    ],
    "Theory": [
        "theorem", "proof", "lemma", "bound", "complexity", "approximation",
        "sample complexity", "generalization", "pac learning",
    ],
    "Diffusion Models": [
        "diffusion", "denoising", "score matching", "noise schedule",
        "score entropy", "discrete diffusion", "continuous diffusion",
    ],
    "Creativity / Generalization": [
        "creativity", "novel", "generalization", "out-of-distribution",
        "compositional", "extrapolation", "interpolation", "combinatorial",
    ],
    "Robotics": [
        "robot", "control", "manipulation", "locomotion", "planning",
        "sensor", "actuator", "simulation",
    ],
    "Security": [
        "adversarial", "attack", "defense", "robustness", "perturbation",
        "vulnerability", "privacy", "differential privacy",
    ],
}

# Common stopwords for keyword extraction
STOPWORDS = set("""
a about above after again against all am an and any are aren't as at be because
been before being below between both but by can't cannot could couldn't did didn't
do does doesn't doing don't down during each few for from further get got had hadn't
has hasn't have haven't having he he'd he'll he's her here here's hers herself him
himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself
let's me more most mustn't my myself no nor not of off on once only or other ought
our ours ourselves out over own same shan't she she'd she'll she's should shouldn't
so some such than that that's the their theirs them themselves then there there's
these they they'd they'll they're they've this those through to too under until up
very was wasn't we we'd we'll we're we've were weren't what what's when when's where
where's which while who who's whom why why's with won't would wouldn't you you'd
you'll you're you've your yours yourself yourselves also use used using one two
three however may many new first well even within et al fig figure table
section paper show shown shows results result method methods approach based model
models work propose proposed propose using given thus therefore hence since although
""".split())


# ── PDF / text extraction ───────────────────────────────────────────────────

def resolve_arxiv_url(url: str) -> str:
    """Convert any arxiv URL to a direct PDF download link."""
    url = url.strip().rstrip("/")
    # Handle abs/ links
    m = re.search(r"arxiv\.org/abs/(\d+\.\d+)", url)
    if m:
        return f"https://arxiv.org/pdf/{m.group(1)}"
    # Already a pdf link
    if "arxiv.org/pdf/" in url:
        if not url.endswith(".pdf"):
            url = url  # arxiv serves PDF without .pdf extension too
        return url
    return url


def download_pdf(url: str) -> str:
    """Download PDF to a temp file and return its path."""
    url = resolve_arxiv_url(url)
    print(f"  Downloading: {url}")
    try:
        resp = requests.get(url, timeout=60, headers={"User-Agent": "ResearchAnalyzer/1.0"})
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise SystemExit(f"Error: could not download PDF.\n  {e}\n\nTip: download the PDF manually and pass the local path instead.")
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(resp.content)
    tmp.close()
    return tmp.name




# ── Analysis helpers ────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Normalize whitespace and strip artifacts."""
    text = re.sub(r"-\n", "", text)          # rejoin hyphenated words
    text = re.sub(r"\n+", " ", text)         # collapse newlines
    text = re.sub(r"\s+", " ", text)         # collapse whitespace
    return text.strip()


def extract_title(text: str) -> str:
    """Heuristic: first substantial lines before the author/abstract block form the title."""
    lines = text.strip().split("\n")
    title_parts = []
    for line in lines[:15]:
        line = line.strip()
        # Stop at author-like lines, abstract, or section headers
        if re.match(r"^(Abstract|arXiv|http|\d+\s)", line, re.I):
            break
        if "@" in line or re.match(r".*\b(University|Institute|Research|Department)\b", line, re.I):
            break
        if len(line) > 10 and not re.match(r"^(Page|\d+$)", line, re.I):
            title_parts.append(line)
        elif title_parts:
            break  # gap after title text
    return " ".join(title_parts) if title_parts else "Unknown Title"


def extract_abstract(text: str) -> str:
    """Pull out the abstract section."""
    # Try to find explicit Abstract header
    m = re.search(
        r"(?:^|\n)\s*Abstract\s*[\n:.\-]\s*(.*?)(?=\n\s*(?:1[\s.]|Introduction|Keywords|I\s))",
        text, re.IGNORECASE | re.DOTALL,
    )
    if m:
        abstract = clean_text(m.group(1))
        # Limit to ~2000 chars
        return abstract[:2000]

    # Fallback: grab first ~1500 chars after "abstract"
    idx = text.lower().find("abstract")
    if idx != -1:
        chunk = text[idx + 8 : idx + 2000]
        return clean_text(chunk)

    return clean_text(text[:1500])


def extract_sections(text: str) -> list[tuple[str, str]]:
    """Extract major section headers and their content."""
    # Match numbered sections like "1 Introduction", "2. Related Work", "3 Methods"
    pattern = r"\n\s*(\d+\.?\s+[A-Z][A-Za-z\s:&,\-]+)\n"
    matches = list(re.finditer(pattern, text))

    sections = []
    for i, match in enumerate(matches):
        header = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections.append((header, body))

    return sections


def tokenize(text: str) -> list[str]:
    """Simple word tokenization."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", " ", text)
    return [w for w in text.split() if len(w) > 2 and w not in STOPWORDS]


def extract_keywords_tfidf(text: str, top_n: int = 20) -> list[tuple[str, float]]:
    """Extract keywords using simple TF-based scoring with bigrams."""
    words = tokenize(text)

    # Unigrams
    unigram_counts = Counter(words)

    # Bigrams
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
    bigram_counts = Counter(bigrams)

    # Score: combine unigrams and bigrams, boost bigrams
    scores = {}
    total = len(words)
    for w, c in unigram_counts.items():
        if c >= 3:  # minimum frequency
            tf = c / total
            # Boost longer, more specific terms
            length_bonus = 1.0 + 0.2 * (len(w) - 3) if len(w) > 5 else 1.0
            scores[w] = tf * length_bonus

    for bg, c in bigram_counts.items():
        if c >= 2:
            tf = c / total
            scores[bg] = tf * 2.5  # bigram boost

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    return ranked[:top_n]


def classify_topics(text: str, top_n: int = 5) -> list[tuple[str, float]]:
    """Classify paper into topics based on keyword matching."""
    text_lower = text.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = 0
        for kw in keywords:
            count = text_lower.count(kw.lower())
            if count > 0:
                # Log-dampen high counts to avoid one keyword dominating
                score += (1 + math.log(count))
        if score > 0:
            scores[topic] = score

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    # Normalize to 0-1
    if ranked:
        max_score = ranked[0][1]
        ranked = [(t, round(s / max_score, 2)) for t, s in ranked]
    return ranked[:top_n]


def extract_methods(text: str) -> list[str]:
    """Detect key methods/techniques mentioned in the paper."""
    method_patterns = [
        r"(?:transformer|attention mechanism|self-attention|multi-head attention)",
        r"(?:next-token prediction|autoregressive|teacher forcing)",
        r"(?:diffusion model|denoising|score matching|score entropy)",
        r"(?:teacherless training|teacherless)",
        r"(?:reinforcement learning|rl|ppo|dpo)",
        r"(?:contrastive learning|simclr|clip)",
        r"(?:fine-tuning|fine tuning|lora|adapter)",
        r"(?:chain-of-thought|cot|reasoning)",
        r"(?:monte carlo|mcts|beam search)",
        r"(?:variational|vae|elbo)",
        r"(?:generative adversarial|gan)",
        r"(?:graph neural|gnn|gcn)",
        r"(?:recurrent|lstm|gru|rnn)",
        r"(?:convolution|cnn|resnet)",
        r"(?:hash.?conditioning|hash function)",
        r"(?:look.?ahead|planning|search)",
    ]
    found = []
    text_lower = text.lower()
    for pat in method_patterns:
        matches = re.findall(pat, text_lower)
        if matches:
            # Use the most common match variant
            best = Counter(matches).most_common(1)[0][0]
            found.append(best.strip())
    return found


def generate_summary(title: str, abstract: str, topics: list, keywords: list, methods: list) -> str:
    """Build a structured text summary."""
    lines = []
    lines.append(f"Title: {title}")
    lines.append("")

    if topics:
        lines.append("Topics:")
        for t, score in topics:
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            lines.append(f"  {bar}  {t} ({score})")
        lines.append("")

    if methods:
        lines.append("Methods / Techniques:")
        for m in methods:
            lines.append(f"  • {m}")
        lines.append("")

    if keywords:
        lines.append("Key Terms:")
        kw_strs = [k for k, _ in keywords[:15]]
        lines.append(f"  {', '.join(kw_strs)}")
        lines.append("")

    if abstract:
        # Produce a condensed version: first 3 sentences
        sentences = re.split(r"(?<=[.!?])\s+", abstract)
        short = " ".join(sentences[:4])
        lines.append("Summary:")
        lines.append(f"  {short}")
        lines.append("")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────

def analyze(source: str) -> str:
    """Analyze a research paper from a URL or local file path."""
    print(f"\n{'═' * 60}")
    print(f"  Research Paper Analyzer")
    print(f"{'═' * 60}\n")

    # Step 1: Get the PDF text
    tmp_path = None
    if source.startswith("http"):
        print("[1/5] Downloading PDF...")
        tmp_path = download_pdf(source)
        pdf_path = tmp_path
    else:
        pdf_path = source
        if not os.path.exists(pdf_path):
            return f"Error: file not found: {pdf_path}"

    print("[2/5] Extracting text...")
    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)
    text = "\n".join(p.extract_text() or "" for p in reader.pages)
    if tmp_path:
        os.unlink(tmp_path)

    if not text or len(text) < 100:
        return "Error: could not extract meaningful text from PDF."

    print(f"       Extracted {len(text):,} characters from {num_pages} pages")

    # Step 2: Extract structure
    print("[3/5] Extracting structure...")
    title = extract_title(text)
    abstract = extract_abstract(text)
    sections = extract_sections(text)

    # Step 3: Classify & extract
    print("[4/5] Classifying topics & extracting keywords...")
    topics = classify_topics(text)
    keywords = extract_keywords_tfidf(text)
    methods = extract_methods(text)

    # Step 4: Build output
    print("[5/5] Generating summary...\n")

    output = generate_summary(title, abstract, topics, keywords, methods)

    if sections:
        output += "Sections:\n"
        for header, _ in sections[:12]:
            output += f"  • {header}\n"
        output += "\n"

    print(output)
    return output


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    source = sys.argv[1]
    analyze(source)


if __name__ == "__main__":
    main()
