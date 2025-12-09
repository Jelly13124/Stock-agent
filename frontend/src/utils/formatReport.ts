/**
 * Clean markdown formatting from report text
 * Removes: ##, **, ___, ---, *, _, etc.
 */
export function cleanMarkdown(text: string): string {
  if (!text) return ''

  return (
    text
      // Remove header markers (##, ###, etc.)
      .replace(/^#{1,6}\s+/gm, '')
      // Remove bold markers (**text** or __text__)
      .replace(/\*\*(.*?)\*\*/g, '$1')
      .replace(/__(.*?)__/g, '$1')
      // Remove italic markers (*text* or _text_)
      .replace(/\*(.*?)\*/g, '$1')
      .replace(/_(.*?)_/g, '$1')
      // Remove horizontal rules (---, ___, ***)
      .replace(/^[\-_*]{3,}$/gm, '')
      // Remove extra empty lines (more than 2 consecutive)
      .replace(/\n{3,}/g, '\n\n')
      // Trim leading/trailing whitespace
      .trim()
  )
}

/**
 * Parse simple markdown-like text into structured sections
 */
export function parseReportSections(text: string): Array<{ title: string; content: string }> {
  if (!text) return []

  const sections: Array<{ title: string; content: string }> = []
  const lines = text.split('\n')
  let currentSection: { title: string; content: string } | null = null

  for (const line of lines) {
    // Check if this is a section header (##, ###, etc.)
    const headerMatch = line.match(/^#{1,6}\s+(.+)$/)
    if (headerMatch) {
      // Save previous section
      if (currentSection) {
        sections.push({
          ...currentSection,
          content: cleanMarkdown(currentSection.content).trim(),
        })
      }
      // Start new section
      currentSection = {
        title: headerMatch[1].trim(),
        content: '',
      }
    } else if (currentSection) {
      // Add line to current section
      currentSection.content += line + '\n'
    }
  }

  // Save last section
  if (currentSection) {
    sections.push({
      ...currentSection,
      content: cleanMarkdown(currentSection.content).trim(),
    })
  }

  return sections.filter((s) => s.content.length > 0)
}

