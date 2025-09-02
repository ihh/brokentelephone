#!/usr/bin/env python3
"""
telephone_tree.py — build an ultrametric binary “telephone game” tree of mutated sentences.

Usage:
  python telephone_tree.py "The books that the world calls immoral are books that show the world its own shame"
    [--depth 5] [--steps-per-branch 10] [--max-retries 3]
    -- [any extra flags to pass through to `llm`]

Notes:
- The ORIGINAL TEXT is a required positional argument.
- `--depth` is the number of mutation *rounds* (levels below the root). depth=5 ⇒ 2^5 leaves.
- `--steps-per-branch` is the number of 1-step mutations per branch (default 10).
- Everything after `--` is passed straight to the `llm` CLI (e.g., `--model gpt-4o-mini --temperature 1.1`).
- Output is printed in **midorder** (inorder: left, node, right). Each line is indented by
  N spaces where N is the number of nodes from that node to the root (root indent=0; leaves indent=depth).
- Requires Simon Willison’s `llm` tool: https://github.com/simonw/llm
"""

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

INSTRUCTION_PROMPT = """You are simulating one single-pass “telephone game” mutation of a sentence.
Goal: make a *small, plausible* change that could arise from mishearing or loose paraphrase in a whisper chain.
Constraints:
- Change should be slight (e.g., a homophone/substitution like "immoral"→"immortal", a near-synonym, a small function-word shift, a light reordering, or one short phrase changed).
- Keep the sentence as one sentence. Preserve approximate length and semantics; do not summarize or expand.
- Avoid profanity, slurs, or adding/removing named entities without reason.
- Output ONLY the mutated sentence (no quotes, no commentary, no prefix/suffix).
Here is the sentence to mutate:

"""

@dataclass
class Node:
    text: str
    depth: int
    left: Optional["Node"] = None
    right: Optional["Node"] = None


def call_llm(prompt: str, llm_args: List[str], max_retries: int = 3, backoff: float = 1.0) -> str:
    """
    Invoke `llm` with a single positional prompt and any pass-through args.
    Retries on non-zero exit codes or empty output.
    """
    last_err = None
    for attempt in range(max_retries):
        try:
            # Build command: llm [llm_args...] PROMPT
            cmd = ["llm", *llm_args, prompt]
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
            )
            out = (proc.stdout or "").strip()
            if proc.returncode == 0 and out:
                # Normalize whitespace to keep it on one line
                return " ".join(out.split())
            last_err = proc.stderr.strip() or f"llm exited with code {proc.returncode}"
        except FileNotFoundError as e:
            last_err = f"Unable to find `llm` on PATH: {e}"
            break
        time.sleep(backoff * (2 ** attempt))
    # Fallback: return the original prompt's last line (the source sentence) if we completely fail.
    # Extract the last non-empty line from the prompt:
    source = ""
    for line in prompt.splitlines()[::-1]:
        line = line.strip()
        if line:
            source = line
            break
    if last_err:
        print(f"# Warning: llm failed after {max_retries} attempts: {last_err}", file=sys.stderr)
    return source  # degrade gracefully


def mutate_once(sentence: str, llm_args: List[str], max_retries: int) -> str:
    prompt = f"{INSTRUCTION_PROMPT}{sentence}"
    mutated = call_llm(prompt, llm_args=llm_args, max_retries=max_retries)
    # Ensure we never return empty:
    return mutated if mutated else sentence


def mutate_chain(sentence: str, steps: int, llm_args: List[str], max_retries: int) -> str:
    """Apply `steps` one-step mutations to sentence, returning the result."""
    current = sentence
    for _ in range(steps):
        current = mutate_once(current, llm_args, max_retries)
    return current


def build_tree(root_text: str, depth: int, steps_per_branch: int, llm_args: List[str], max_retries: int) -> Node:
    """
    Build a perfectly balanced binary tree to the given depth.
    Each edge applies `steps_per_branch` sequential one-step mutations (`g`).
    """
    root = Node(text=root_text, depth=0)

    def expand(node: Node):
        if node.depth >= depth:
            return
        # Generate two children from the same parent text, each via g(·)
        left_text = mutate_chain(node.text, steps_per_branch, llm_args, max_retries)
        right_text = mutate_chain(node.text, steps_per_branch, llm_args, max_retries)
        node.left = Node(text=left_text, depth=node.depth + 1)
        node.right = Node(text=right_text, depth=node.depth + 1)
        expand(node.left)
        expand(node.right)

    expand(root)
    return root


def inorder_print(node: Optional[Node]):
    """Midorder (inorder) traversal: left, node, right. Indent by node.depth spaces."""
    if not node:
        return
    inorder_print(node.left)
    indent = " " * node.depth
    print(f"{indent}{node.text}")
    inorder_print(node.right)


def parse_args(argv: List[str]):
    parser = argparse.ArgumentParser(description="Generate an ultrametric telephone-mutation tree using `llm`.")
    parser.add_argument("original_text", help="The original sentence to mutate (X).")
    parser.add_argument("--depth", type=int, default=5,
                        help="Number of mutation rounds (levels below root). Default: 5 (32 leaves).")
    parser.add_argument("--steps-per-branch", type=int, default=10,
                        help="Number of one-step mutations per edge (g = f^k). Default: 10.")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Retries for llm failures. Default: 3.")
    # Everything after `--` goes to `llm`
    args, passthrough = parser.parse_known_args(argv)

    # Strip a leading '--' separator if present (argparse keeps it)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    return args, passthrough


def main(argv: List[str]):
    args, llm_args = parse_args(argv)
    root = build_tree(
        root_text=args.original_text,
        depth=args.depth,
        steps_per_branch=args.steps_per_branch,
        llm_args=llm_args,
        max_retries=args.max_retries,
    )
    inorder_print(root)


if __name__ == "__main__":
    main(sys.argv[1:])
