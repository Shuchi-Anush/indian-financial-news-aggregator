import { Article } from '@/types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export function ArticleCard({ article }: { article: Article }) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex justify-between items-start gap-4">
          <CardTitle className="text-lg line-clamp-2">
            <a href={article.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
              {article.title}
            </a>
          </CardTitle>
          <Badge variant="outline">{article.source_name}</Badge>
        </div>
        <CardDescription>
          {new Date(article.published_at).toLocaleDateString()}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1">
        <p className="text-sm text-muted-foreground line-clamp-3">{article.summary || 'No summary available.'}</p>
      </CardContent>
      <CardFooter className="text-xs text-muted-foreground flex justify-between">
        <span>{article.category}</span>
        {article.sentiment_label && <span>Sentiment: {article.sentiment_label}</span>}
      </CardFooter>
    </Card>
  );
}
