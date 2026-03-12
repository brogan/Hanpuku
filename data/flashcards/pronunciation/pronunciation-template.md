# Pronunciation Flashcard Template

This template is for creating pronunciation flashcards that extend beyond basic kana forms.
Use this format for multi-kana sequences, long vowels, double consonants, and other pronunciation patterns.

## How to Use This Template

When creating pronunciation flashcards with Claude.ai, reference this template and specify:
1. The kana sequence(s) you want to practice
2. Any specific categories or themes (e.g., long vowels, double consonants, common word patterns)

## Card Format

Each pronunciation card follows this structure:

```markdown
---
## [Kana Sequence]

**Reading:** [Romaji pronunciation]
**Meaning:** [Romaji pronunciation]
**Type:** pronunciation
**Level:** N5
**Tags:** [relevant tags - see below]

### Notes
[Optional: pronunciation tips, common words using this pattern]

---
```

## Available Tags

Use these tags to categorize pronunciation cards:

### Sound Type Tags
- `#long-vowel` - Extended vowel sounds (おう, えい, etc.)
- `#double-consonant` - Small tsu (っ) patterns
- `#nasal` - Sounds involving ん
- `#combo` - Multi-syllable combinations

### Pattern Tags
- `#common-pattern` - Frequently occurring in Japanese
- `#loanword-pattern` - Common in katakana loanwords
- `#verb-ending` - Common verb conjugation patterns
- `#adjective-ending` - Common adjective patterns

### Difficulty Tags
- `#beginner` - Simple combinations
- `#intermediate` - More complex patterns
- `#advanced` - Rare or difficult combinations

---

## Example Cards

Below are example pronunciation cards demonstrating the format:

---
## おう

**Reading:** ou / ō
**Meaning:** ou / ō
**Type:** pronunciation
**Level:** N5
**Tags:** #long-vowel, #common-pattern, #beginner

### Notes
Long "o" sound. Common in words like おうさま (king), おとうさん (father).
Often written as "ō" in romaji.

---
## えい

**Reading:** ei / ē
**Meaning:** ei / ē
**Type:** pronunciation
**Level:** N5
**Tags:** #long-vowel, #common-pattern, #beginner

### Notes
Long "e" sound. Common in words like せんせい (teacher), えいご (English).
Sometimes pronounced closer to "ee" in casual speech.

---
## っか

**Reading:** kka
**Meaning:** kka
**Type:** pronunciation
**Level:** N5
**Tags:** #double-consonant, #common-pattern, #beginner

### Notes
Double consonant with small tsu (っ). Creates a brief pause before the "k" sound.
Example: がっこう (school), さっか (writer).

---
## っち

**Reading:** tchi
**Meaning:** tchi
**Type:** pronunciation
**Level:** N5
**Tags:** #double-consonant, #common-pattern, #beginner

### Notes
Double consonant before "chi" sound.
Example: まっち (match), きっちん (kitchen).

---
## っぷ

**Reading:** ppu
**Meaning:** ppu
**Type:** pronunciation
**Level:** N5
**Tags:** #double-consonant, #common-pattern, #beginner

### Notes
Double consonant before "pu" sound.
Example: いっぷん (one minute), コップ (cup).

---
## んか

**Reading:** nka
**Meaning:** nka
**Type:** pronunciation
**Level:** N5
**Tags:** #nasal, #common-pattern, #beginner

### Notes
Nasal "n" before "ka". The ん takes on a slight "ng" quality.
Example: げんかん (entrance), さんか (participation).

---
## んぱ

**Reading:** npa
**Meaning:** npa
**Type:** pronunciation
**Level:** N5
**Tags:** #nasal, #common-pattern, #beginner

### Notes
Nasal "n" before "pa". The ん sounds more like "m" before p/b/m sounds.
Example: さんぽ (walk), しんぱい (worry).

---
## ティ

**Reading:** ti
**Meaning:** ti
**Type:** pronunciation
**Level:** N5
**Tags:** #loanword-pattern, #katakana, #intermediate

### Notes
Modern katakana combination for "ti" sound in loanwords.
Example: パーティー (party), ティッシュ (tissue).

---
## ファ

**Reading:** fa
**Meaning:** fa
**Type:** pronunciation
**Level:** N5
**Tags:** #loanword-pattern, #katakana, #intermediate

### Notes
Modern katakana combination for "fa" sound in loanwords.
Example: ファン (fan), ソファ (sofa).

---
## ウィ

**Reading:** wi
**Meaning:** wi
**Type:** pronunciation
**Level:** N5
**Tags:** #loanword-pattern, #katakana, #intermediate

### Notes
Modern katakana combination for "wi" sound in loanwords.
Example: ウィンドウ (window), サンドウィッチ (sandwich).

---

## Requesting Pronunciation Cards from Claude.ai

When asking Claude.ai to create pronunciation flashcards, you can say:

"Please create pronunciation flashcards for [specific patterns] using the template in:
/Users/broganbunt/python_work/SRS/data/flashcards/pronunciation/pronunciation-template.md

Include patterns such as:
- [list specific patterns you want]
- [or describe the theme/category]

Save to: /Users/broganbunt/python_work/SRS/data/flashcards/pronunciation/[filename].md"

### Example Requests:

1. "Create pronunciation cards for all double consonant patterns (っ + consonant)"

2. "Create pronunciation cards for common verb endings (-ます, -ました, -ません, etc.)"

3. "Create pronunciation cards for long vowel combinations in common words"

4. "Create pronunciation cards for modern katakana loanword sounds (ティ, ファ, ウィ, etc.)"

---
