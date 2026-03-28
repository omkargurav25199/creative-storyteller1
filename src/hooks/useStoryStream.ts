import { useState, useCallback } from 'react';

export function useStoryStream() {
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL!;

  const [title, setTitle] = useState('');
  const [blocks, setBlocks] = useState<any[]>([]);
  const [status, setStatus] = useState<'idle' | 'generating' | 'complete' | 'error'>('idle');

  const generate = useCallback(async (
    prompt: string,
    style: string,
    audience: string,
    numScenes: number,
  ) => {
    setTitle('');
    setBlocks([]);
    setStatus('generating');

    try {
      const res = await fetch(`${backendUrl}/api/v1/stories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, style, audience, numScenes }),
      });

      const { streamUrl } = await res.json();
      const evt = new EventSource(`${backendUrl}${streamUrl}`);

      evt.addEventListener('story_meta', (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        setTitle(data.title);
      });

      evt.addEventListener('content_block', (e) => {
        const data = JSON.parse((e as MessageEvent).data);
        setBlocks(prev => [
          ...prev,
          {
            sceneId: data.sceneId,
            type: data.type,
            content: data.type === 'text' ? data.text : data.url,
          }
        ]);
      });

      evt.addEventListener('done', () => {
        evt.close();
        setStatus('complete');
      });

      evt.onerror = () => {
        evt.close();
        setStatus('error');
      };

    } catch {
      setStatus('error');
    }
  }, [backendUrl]);

  return { title, blocks, status, generate };
}