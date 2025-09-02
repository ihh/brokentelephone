#!/usr/bin/env python3
"""
telephone_tree.py — build an ultrametric binary “telephone game” tree of mutated sentences.

Usage:
  python telephone_tree.py "The books that the world calls immoral are books that show the world its own shame"
    [--depth 5] [--steps-per-branch 1] [--max-retries 3]
    -- [any extra flags to pass through to `llm`]

Notes:
- The ORIGINAL TEXT is a required positional argument.
- `--depth` is the number of mutation *rounds* (levels below the root). depth=5 ⇒ 2^5 leaves.
- `--steps-per-branch` is the number of 1-step mutations per branch (default 1).
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

def INSTRUCTION_PROMPT(distance: str) -> str:
    return f"""Simulate a single-pass “telephone game” mutation of a sentence.

Rules:
- Make a plausible change as if misheard or loosely rephrased in a whisper.
- Prioritize prosodic equivalence: homophones, near-homophones, or words with the same stressed vowel (e.g. “give”→“bring”→“deliver”). Slightly longer/faster-spoken words are acceptable if the rhythm feels natural.
- Substitutions can also be near-synonyms, function-word shifts, or minor reorderings. However, mishearing (same sound, different meaning) is preferred over rephrasing (same meaning, different sound). A light semantic drift or touch of absurdity is fine.
- Limit the change to ~{distance} small edits; preserve overall length, rhythm, and coherence.
- Do not summarize, expand, or add named entities. Avoid profanity or slurs.
- Output ONLY the mutated sentence (no quotes, no commentary, no prefix/suffix, no extra words; do not repeat the original sentence as well).
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
                return " ".join(out.split())
            last_err = proc.stderr.strip() or f"llm exited with code {proc.returncode}"
        except FileNotFoundError as e:
            last_err = f"Unable to find `llm` on PATH: {e}"
            break
        time.sleep(backoff * (2 ** attempt))
    # fallback
    source = ""
    for line in prompt.splitlines()[::-1]:
        line = line.strip()
        if line:
            source = line
            break
    if last_err:
        print(f"# Warning: llm failed after {max_retries} attempts: {last_err}", file=sys.stderr)
    return source


def mutate_once(sentence: str, prompt_distance: int, llm_args: List[str], max_retries: int) -> str:
    
    prompt = f"{INSTRUCTION_PROMPT(prompt_distance)}{sentence}"
    mutated = call_llm(prompt, llm_args=llm_args, max_retries=max_retries)
    return mutated if mutated else sentence


def mutate_chain(sentence: str, steps: int, prompt_distance: int, llm_args: List[str], max_retries: int, prefix: str = "") -> str:
    """Apply `steps` one-step mutations to sentence, returning the result."""
    current = sentence
    for i in range(steps):
        print(f"[progress] {prefix} step {i+1}/{steps}: {current}", file=sys.stderr)
        current = mutate_once(current, prompt_distance, llm_args, max_retries)
    print(f"[progress] {prefix} final: {current}", file=sys.stderr)
    return current


def build_tree(root_text: str, depth: int, steps_per_branch: int, prompt_distance: int, llm_args: List[str], max_retries: int) -> Node:
    root = Node(text=root_text, depth=0)

    def expand(node: Node, path: str = "root"):
        if node.depth >= depth:
            return
        print(f"[progress] Expanding {path} at depth {node.depth}", file=sys.stderr)
        left_text = mutate_chain(node.text, steps_per_branch, prompt_distance, llm_args, max_retries, prefix=f"{path}-L")
        right_text = mutate_chain(node.text, steps_per_branch, prompt_distance, llm_args, max_retries, prefix=f"{path}-R")
        node.left = Node(text=left_text, depth=node.depth + 1)
        node.right = Node(text=right_text, depth=node.depth + 1)
        expand(node.left, path=f"{path}-L")
        expand(node.right, path=f"{path}-R")

    expand(root)
    return root


def inorder_print(node: Optional[Node]):
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
    parser.add_argument("--steps-per-branch", type=int, default=1,
                        help="Number of one-step mutations per edge. Default: 1.")
    parser.add_argument("--prompt-distance", type=str, default="1-3",
                        help="Description of the number of edits per mutation, fed to the LLM as a prompt. Default: '1-3'.")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Retries for llm failures. Default: 3.")
    args, passthrough = parser.parse_known_args(argv)
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]
    return args, passthrough


def main(argv: List[str]):
    args, llm_args = parse_args(argv)
    print(f"[progress] Building tree with depth={args.depth}, steps_per_branch={args.steps_per_branch}", file=sys.stderr)
    root = build_tree(
        root_text=args.original_text,
        depth=args.depth,
        steps_per_branch=args.steps_per_branch,
        prompt_distance=args.prompt_distance,
        llm_args=llm_args,
        max_retries=args.max_retries,
    )
    inorder_print(root)


if __name__ == "__main__":
    main(sys.argv[1:])
